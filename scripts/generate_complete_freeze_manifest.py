"""
Script to generate the complete, authoritative SHA-256 frozen artifact manifest
for QUANTUM Phase 5.3.7.1 in artifacts/phase_5_3_freeze/frozen_artifact_manifest.json.
Categorizes all 304+ frozen files produced across Phase 5.3.1 through Phase 5.3.3.6.
"""

import hashlib
import json
from pathlib import Path


def categorize_artifact(path_str: str) -> tuple[str, str, str]:
    """Return (artifact_category, producing_phase, description)."""
    p = path_str.lower()
    
    if "phase_5_3_1" in p:
        phase = "Phase 5.3.1 Pilot"
    elif "phase_5_3_2" in p:
        phase = "Phase 5.3.2 Expanded Fleet"
    elif "phase_5_3_3_1" in p:
        phase = "Phase 5.3.3.1 Final Benchmark Correction"
    elif "phase_5_3_3_2" in p:
        phase = "Phase 5.3.3.2 Independent Statistical Verification"
    elif "phase_5_3_3_3" in p:
        phase = "Phase 5.3.3.3 Empirical OOF Resampling"
    elif "phase_5_3_3_4" in p:
        phase = "Phase 5.3.3.4 Metric Reconciliation"
    elif "phase_5_3_3_5" in p:
        phase = "Phase 5.3.3.5 Paired B4-B0 Audit"
    elif "phase_5_3_3_6" in p:
        phase = "Phase 5.3.3.6 Final Population & Bootstrap Audit"
    elif "phase_5_3_3" in p:
        phase = "Phase 5.3.3 Master Benchmark Audit"
    else:
        phase = "Phase 5.3 Architecture"

    if "lgbm_model.joblib" in p:
        return "model_binary", phase, "Frozen B4 LightGBM Specialist Model Binary"
    elif "preprocessor.joblib" in p:
        return "preprocessor", phase, "Frozen Specialist Preprocessor Pipeline"
    elif "metrics.json" in p:
        return "evaluation_metrics", phase, "Fold-Level Model Evaluation Metrics"
    elif "confusion_matrix.json" in p:
        return "confusion_matrix", phase, "Fold-Level Contingency Matrix"
    elif "predictions.parquet" in p or "predictions.csv" in p:
        return "oof_predictions", phase, "Candle-Level Out-of-Fold Model Predictions and Probabilities"
    elif "summary.json" in p or "pilot_summary.json" in p or "fleet_catalog.json" in p or "fleet_comparison.json" in p:
        return "metadata_manifest", phase, "Summary and Provenance Metadata Manifest"
    elif "benchmark_catalog" in p:
        return "benchmark_catalog", phase, "Authoritative Benchmark Performance Catalog"
    elif "bootstrap" in p or "mbb" in p:
        return "bootstrap_audit", phase, "Resampling Sensitivity and Bootstrap Inference Output"
    elif "paired" in p or "fold_aggregation" in p:
        return "paired_audit", phase, "Paired B4 vs B0 Statistical Audit Output"
    elif "population" in p or "sample_accounting" in p:
        return "population_audit", phase, "OOF Sample Population Accounting and Audit Output"
    elif "manifest" in p or "hash" in p:
        return "integrity_manifest", phase, "Cryptographic Checksum and Hash Manifest"
    else:
        return "supporting_audit_artifact", phase, "Supporting Validation and Governance Artifact"


def main():
    art_dir = Path("artifacts")
    output_dir = art_dir / "phase_5_3_freeze"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "frozen_artifact_manifest.json"

    artifacts = []
    category_counts = {}
    phase_counts = {}

    for p in sorted(art_dir.glob("**/*")):
        if p.is_file():
            # Skip the manifest itself if regenerating
            if p == output_file:
                continue
            
            rel_path = p.as_posix()
            file_size = p.stat().st_size
            sha256_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            
            cat, phase, desc = categorize_artifact(rel_path)
            category_counts[cat] = category_counts.get(cat, 0) + 1
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

            artifacts.append({
                "relative_path": rel_path,
                "file_size_bytes": file_size,
                "sha256": sha256_hash,
                "artifact_category": cat,
                "producing_phase": phase,
                "description": desc,
                "freeze_status": "FROZEN_IMMUTABLE"
            })

    manifest_data = {
        "manifest_version": "5.3.7.1_COMPLETE",
        "title": "QUANTUM Phase 5.3 Complete Frozen Artifact Manifest",
        "description": "Exhaustive cryptographic inventory of all model binaries, preprocessors, predictions, evaluations, and audit artifacts across Phase 5.3.",
        "governance_verdict": "PHASE_5_3_FREEZE_COMPLETE",
        "total_artifacts_cataloged": len(artifacts),
        "category_summary": category_counts,
        "phase_summary": phase_counts,
        "model_binaries_count": category_counts.get("model_binary", 0),
        "preprocessors_count": category_counts.get("preprocessor", 0),
        "artifacts": artifacts
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Successfully generated {output_file}")
    print(f"Total artifacts cataloged: {len(artifacts)}")
    print(f"Model binaries (B4): {category_counts.get('model_binary', 0)}")
    print(f"Preprocessors: {category_counts.get('preprocessor', 0)}")
    print("Categories:", json.dumps(category_counts, indent=2))
    print("Phases:", json.dumps(phase_counts, indent=2))


if __name__ == "__main__":
    main()
