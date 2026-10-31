"""UI tests for Workspace 3 (AgentsPage) cards, telemetry, and model registry view."""

import pytest
from PySide6.QtWidgets import QApplication

from quantum.domain.enums import AgentId, ModelStatus
from quantum.ml.registry import FEATURE_SCHEMA_V1_HASH, ModelManifest, ModelRegistry
from quantum.ui.pages.agents_page import AgentsPage


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_agents_page_initialization(qapp: QApplication) -> None:
    page = AgentsPage()
    assert page is not None
    assert len(page._agent_cards) == 5
    for name in ["SCOUT", "ANALYST", "SNIPER", "RISK", "BANKER"]:
        assert name in page._agent_cards
        card = page._agent_cards[name]
        assert "Latency: 0.0 ms" in card["latency"].text()
        assert "Runs: 0" in card["runs"].text()

    # Initial state should show cold start empty state
    assert page.registry_stack.currentIndex() == 0


def test_agents_page_update_metrics(qapp: QApplication) -> None:
    page = AgentsPage()

    page.update_agent_metrics(
        agent_name="SCOUT",
        latency_ms=1.4,
        runs=12,
        proposals=8,
        vetos=4,
        model_version="scout_lgb_v1.0",
        mode="LOCAL_ML",
    )

    card = page._agent_cards["SCOUT"]
    assert "Latency: 1.4 ms" in card["latency"].text()
    assert "Runs: 12 | Props: 8 | Vetos: 4" in card["runs"].text()
    assert "Model: scout_lgb_v1.0" in card["model"].text()
    assert "[LOCAL_ML]" in card["mode"].text()


def test_agents_page_registry_refresh(qapp: QApplication) -> None:
    page = AgentsPage()
    registry = ModelRegistry()

    # 1. Empty registry -> empty state
    page.refresh_registry(registry)
    assert page.registry_stack.currentIndex() == 0

    # 2. Add model manifest -> table view
    manifest = ModelManifest(
        model_version="analyst_xgb_v1",
        agent_id=AgentId.ANALYST,
        algorithm="LightGBM",
        feature_schema_hash=FEATURE_SCHEMA_V1_HASH,
        artifact_dir_path="",
        artifact_sha256="c" * 64,
        decision_threshold=0.58,
        created_at_ms=1700000000000,
    )
    registry.register_model(manifest, status=ModelStatus.PRODUCTION)

    page.refresh_registry(registry)
    assert page.registry_stack.currentIndex() == 1
    assert page.models_table.rowCount() == 1
    assert page.models_table.item(0, 0).text() == "analyst_xgb_v1"
    assert page.models_table.item(0, 1).text() == "ANALYST"
    assert page.models_table.item(0, 3).text() == "PRODUCTION"
