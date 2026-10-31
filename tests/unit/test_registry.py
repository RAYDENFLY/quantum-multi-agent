"""Unit tests for local ModelRegistry and artifact integrity verification."""

from pathlib import Path
import pytest

from quantum.domain.enums import AgentId, ModelStatus
from quantum.ml.registry import (
    CorruptedModelError,
    FEATURE_SCHEMA_V1_HASH,
    IncompatibleSchemaError,
    ModelManifest,
    ModelRegistry,
    ModelUnavailableError,
)


def test_schema_hash_validation() -> None:
    # Valid canonical schema hash
    manifest = ModelManifest(
        model_version="scout_xgb_v1",
        agent_id=AgentId.SCOUT,
        algorithm="LightGBM_C++_Booster",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="d" * 64,
        decision_threshold=0.56,
        created_at_ms=1700000000000,
    )
    assert manifest.model_version == "scout_xgb_v1"

    # Incompatible schema hash raises IncompatibleSchemaError
    with pytest.raises(IncompatibleSchemaError):
        ModelManifest(
            model_version="scout_xgb_bad_schema",
            agent_id=AgentId.SCOUT,
            algorithm="LightGBM_C++_Booster",
            feature_schema_hash="0123456789abcdef" * 4,
            artifact_dir_path="",
            artifact_sha256="d" * 64,
            decision_threshold=0.56,
            created_at_ms=1700000000000,
        )


def test_artifact_sha256_checksum_verification(tmp_path: Path) -> None:
    registry = ModelRegistry()

    # Create dummy artifact directory with a model file
    artifact_dir = tmp_path / "scout_v1"
    artifact_dir.mkdir()
    model_file = artifact_dir / "model.txt"
    model_file.write_text("model_binary_content_bytes")

    correct_hash = registry.compute_dir_hash(artifact_dir)

    manifest_valid = ModelManifest(
        model_version="scout_xgb_v1",
        agent_id=AgentId.SCOUT,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path=str(artifact_dir),
        artifact_sha256=correct_hash,
        decision_threshold=0.56,
        created_at_ms=1700000000000,
    )

    metadata = registry.register_model(manifest_valid, status=ModelStatus.CANDIDATE)
    assert metadata.model_version == "scout_xgb_v1"
    assert metadata.status == ModelStatus.CANDIDATE

    # Corrupt artifact: wrong checksum
    manifest_corrupt = ModelManifest(
        model_version="scout_xgb_corrupt",
        agent_id=AgentId.SCOUT,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path=str(artifact_dir),
        artifact_sha256="0" * 64,  # Mismatch!
        decision_threshold=0.56,
        created_at_ms=1700000000000,
    )

    with pytest.raises(CorruptedModelError, match="Checksum mismatch"):
        registry.register_model(manifest_corrupt)


def test_model_promotion_and_demotion_lifecycle() -> None:
    registry = ModelRegistry()

    m1 = ModelManifest(
        model_version="analyst_lgb_v1",
        agent_id=AgentId.ANALYST,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="a" * 64,
        decision_threshold=0.58,
        created_at_ms=1700000000000,
    )
    m2 = ModelManifest(
        model_version="analyst_lgb_v2",
        agent_id=AgentId.ANALYST,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="b" * 64,
        decision_threshold=0.60,
        created_at_ms=1700000001000,
    )

    registry.register_model(m1, status=ModelStatus.CANDIDATE)
    registry.register_model(m2, status=ModelStatus.CANDIDATE)

    # Initially candidate, active model lookup in FALLBACK_RULE_ONLY returns None
    assert registry.get_active_model(AgentId.ANALYST, fallback_policy="FALLBACK_RULE_ONLY") is None

    # In STRICT_ML_ONLY, raises ModelUnavailableError
    with pytest.raises(ModelUnavailableError):
        registry.get_active_model(AgentId.ANALYST, fallback_policy="STRICT_ML_ONLY")

    # Promote m1
    promoted_1 = registry.promote_model("analyst_lgb_v1")
    assert promoted_1.status == ModelStatus.PRODUCTION
    active = registry.get_active_model(AgentId.ANALYST)
    assert active is not None
    assert active.model_version == "analyst_lgb_v1"

    # Promote m2 -> m1 automatically demoted to ARCHIVED
    promoted_2 = registry.promote_model("analyst_lgb_v2")
    assert promoted_2.status == ModelStatus.PRODUCTION

    models = {m.model_version: m for m in registry.list_models(AgentId.ANALYST)}
    assert models["analyst_lgb_v1"].status == ModelStatus.ARCHIVED
    assert models["analyst_lgb_v2"].status == ModelStatus.PRODUCTION
    assert registry.get_active_model(AgentId.ANALYST).model_version == "analyst_lgb_v2"

    # Test Rollback: rollback analyst promotion
    restored = registry.rollback_promotion(AgentId.ANALYST)
    assert restored is not None
    assert restored.model_version == "analyst_lgb_v1"
    assert restored.status == ModelStatus.PRODUCTION
    assert registry.get_active_model(AgentId.ANALYST).model_version == "analyst_lgb_v1"
    assert registry.list_models(AgentId.ANALYST)[1].status == ModelStatus.REJECTED

    # Rollback again: no prior archived model left -> falls back to None (RULE_ONLY)
    restored_none = registry.rollback_promotion(AgentId.ANALYST)
    assert restored_none is None
    assert registry.get_active_model(AgentId.ANALYST, fallback_policy="FALLBACK_RULE_ONLY") is None


def test_concurrent_registry_access() -> None:
    import concurrent.futures
    registry = ModelRegistry()

    m = ModelManifest(
        model_version="sniper_xgb_v1",
        agent_id=AgentId.SNIPER,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="c" * 64,
        decision_threshold=0.25,
        created_at_ms=1700000000000,
    )
    registry.register_model(m, status=ModelStatus.PRODUCTION)

    def reader() -> int:
        count = 0
        for _ in range(50):
            model = registry.get_active_model(AgentId.SNIPER)
            if model is not None:
                count += 1
            registry.list_models()
        return count

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(reader) for _ in range(8)]
        results = [f.result() for f in futures]

    assert all(r == 50 for r in results)


def test_registry_successful_rollback() -> None:
    registry = ModelRegistry()

    m1 = ModelManifest(
        model_version="scout_v1",
        agent_id=AgentId.SCOUT,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="1" * 64,
        decision_threshold=0.56,
        created_at_ms=1700000000000,
    )
    m2 = ModelManifest(
        model_version="scout_v2",
        agent_id=AgentId.SCOUT,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="2" * 64,
        decision_threshold=0.56,
        created_at_ms=1700000001000,
    )
    registry.register_model(m1, status=ModelStatus.CANDIDATE)
    registry.register_model(m2, status=ModelStatus.CANDIDATE)

    # Promote v1
    registry.promote_model("scout_v1")
    assert registry.get_active_model(AgentId.SCOUT).model_version == "scout_v1"

    # Promote v2 (v1 moves to ARCHIVED)
    registry.promote_model("scout_v2")
    assert registry.get_active_model(AgentId.SCOUT).model_version == "scout_v2"

    # Rollback: v2 -> REJECTED, v1 restored to PRODUCTION
    restored = registry.rollback_promotion(AgentId.SCOUT)
    assert restored is not None
    assert restored.model_version == "scout_v1"
    assert restored.status == ModelStatus.PRODUCTION
    assert registry.get_active_model(AgentId.SCOUT).model_version == "scout_v1"

    # Verify model statuses
    models = {m.model_version: m for m in registry.list_models(AgentId.SCOUT)}
    assert models["scout_v1"].status == ModelStatus.PRODUCTION
    assert models["scout_v2"].status == ModelStatus.REJECTED

    # Invariant: exactly one model marked PRODUCTION
    prod = [m for m in registry.list_models(AgentId.SCOUT) if m.status == ModelStatus.PRODUCTION]
    assert len(prod) == 1


def test_registry_rollback_with_no_previous_model() -> None:
    registry = ModelRegistry()

    m1 = ModelManifest(
        model_version="analyst_only_v1",
        agent_id=AgentId.ANALYST,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="3" * 64,
        decision_threshold=0.58,
        created_at_ms=1700000000000,
    )
    registry.register_model(m1, status=ModelStatus.PRODUCTION)
    assert registry.get_active_model(AgentId.ANALYST).model_version == "analyst_only_v1"

    # Rollback when no previous archived model exists
    restored = registry.rollback_promotion(AgentId.ANALYST)
    assert restored is None

    # Verify fallback to rule-only baseline
    assert registry.get_active_model(AgentId.ANALYST, fallback_policy="FALLBACK_RULE_ONLY") is None

    # In STRICT_ML_ONLY, raises ModelUnavailableError
    with pytest.raises(ModelUnavailableError):
        registry.get_active_model(AgentId.ANALYST, fallback_policy="STRICT_ML_ONLY")

    # Invariant: exactly zero models marked PRODUCTION
    prod = [m for m in registry.list_models(AgentId.ANALYST) if m.status == ModelStatus.PRODUCTION]
    assert len(prod) == 0


def test_registry_repeated_rollback_sequence() -> None:
    registry = ModelRegistry()

    manifests = [
        ModelManifest(
            model_version=f"sniper_seq_v{i}",
            agent_id=AgentId.SNIPER,
            algorithm="LightGBM",
            feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
            artifact_dir_path="",
            artifact_sha256=f"{i}" * 64,
            decision_threshold=0.25,
            created_at_ms=1700000000000 + (i * 1000),
        )
        for i in range(1, 4)
    ]

    for m in manifests:
        registry.register_model(m, status=ModelStatus.CANDIDATE)

    # Sequentially promote v1, v2, v3
    registry.promote_model("sniper_seq_v1")
    registry.promote_model("sniper_seq_v2")
    registry.promote_model("sniper_seq_v3")
    assert registry.get_active_model(AgentId.SNIPER).model_version == "sniper_seq_v3"

    # 1st Rollback: v3 -> REJECTED, restores v2
    r1 = registry.rollback_promotion(AgentId.SNIPER)
    assert r1 is not None
    assert r1.model_version == "sniper_seq_v2"
    assert registry.get_active_model(AgentId.SNIPER).model_version == "sniper_seq_v2"
    assert len([m for m in registry.list_models(AgentId.SNIPER) if m.status == ModelStatus.PRODUCTION]) == 1

    # 2nd Rollback: v2 -> REJECTED, restores v1
    r2 = registry.rollback_promotion(AgentId.SNIPER)
    assert r2 is not None
    assert r2.model_version == "sniper_seq_v1"
    assert registry.get_active_model(AgentId.SNIPER).model_version == "sniper_seq_v1"
    assert len([m for m in registry.list_models(AgentId.SNIPER) if m.status == ModelStatus.PRODUCTION]) == 1

    # 3rd Rollback: v1 -> REJECTED, restores None (rule-only fallback)
    r3 = registry.rollback_promotion(AgentId.SNIPER)
    assert r3 is None
    assert registry.get_active_model(AgentId.SNIPER) is None
    assert len([m for m in registry.list_models(AgentId.SNIPER) if m.status == ModelStatus.PRODUCTION]) == 0

    # 4th Rollback: when already None, cleanly returns None without crashing
    r4 = registry.rollback_promotion(AgentId.SNIPER)
    assert r4 is None
    assert registry.get_active_model(AgentId.SNIPER) is None


def test_registry_rollback_state_integrity_and_single_production_invariant() -> None:
    registry = ModelRegistry()

    # Register multiple models for SCOUT and ANALYST
    for agent, versions in [(AgentId.SCOUT, ["scout_a", "scout_b"]), (AgentId.ANALYST, ["analyst_a", "analyst_b"])]:
        for v in versions:
            m = ModelManifest(
                model_version=v,
                agent_id=agent,
                algorithm="LightGBM",
                feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
                artifact_dir_path="",
                artifact_sha256="f" * 64,
                decision_threshold=0.50,
                created_at_ms=1700000000000,
            )
            registry.register_model(m, status=ModelStatus.CANDIDATE)

    # Invariant checker helper
    def verify_invariants() -> None:
        for agent in [AgentId.SCOUT, AgentId.ANALYST]:
            prod = [m for m in registry.list_models(agent) if m.status == ModelStatus.PRODUCTION]
            assert len(prod) <= 1, f"Multiple models marked PRODUCTION for agent {agent}!"
            active = registry.get_active_model(agent)
            if len(prod) == 1:
                assert active is not None
                assert active.model_version == prod[0].model_version
            else:
                assert active is None

    verify_invariants()
    registry.promote_model("scout_a")
    verify_invariants()
    registry.promote_model("analyst_a")
    verify_invariants()
    registry.promote_model("scout_b")
    verify_invariants()
    registry.rollback_promotion(AgentId.SCOUT)
    verify_invariants()
    registry.rollback_promotion(AgentId.SCOUT)
    verify_invariants()
    registry.rollback_promotion(AgentId.ANALYST)
    verify_invariants()


def test_registry_concurrent_promotion_and_rollback_safety() -> None:
    import concurrent.futures
    registry = ModelRegistry()

    # Register 4 models for SNIPER
    for i in range(1, 5):
        m = ModelManifest(
            model_version=f"sniper_conc_v{i}",
            agent_id=AgentId.SNIPER,
            algorithm="LightGBM",
            feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
            artifact_dir_path="",
            artifact_sha256=f"{i}" * 64,
            decision_threshold=0.25,
            created_at_ms=1700000000000 + (i * 100),
        )
        registry.register_model(m, status=ModelStatus.CANDIDATE)

    def worker(worker_id: int) -> int:
        operations = 0
        for i in range(25):
            ver = f"sniper_conc_v{(i % 4) + 1}"
            if worker_id % 2 == 0:
                try:
                    registry.promote_model(ver)
                except Exception:
                    pass
            else:
                registry.rollback_promotion(AgentId.SNIPER)
            active = registry.get_active_model(AgentId.SNIPER)
            models = registry.list_models(AgentId.SNIPER)
            prod = [m for m in models if m.status == ModelStatus.PRODUCTION]
            assert len(prod) <= 1, f"Invariant violated in worker {worker_id}!"
            operations += 1
        return operations

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, w) for w in range(8)]
        results = [f.result() for f in futures]

    assert all(r == 25 for r in results)
    final_prod = [m for m in registry.list_models(AgentId.SNIPER) if m.status == ModelStatus.PRODUCTION]
    assert len(final_prod) <= 1

