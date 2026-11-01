#!/usr/bin/env python3
"""Standalone verification script for Phase 5.3.3.1 cryptographic manifest.

Reads artifacts/phase_5_3_3_1/final_manifest_hashes.json and validates the
SHA-256 hash of each artifact on disk.
"""

import hashlib
import json
import sys
from pathlib import Path

def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_manifest() -> bool:
    manifest_path = Path("artifacts/phase_5_3_3_1/final_manifest_hashes.json")
    if not manifest_path.exists():
        print(f"FAIL: Manifest not found at {manifest_path}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_matched = True
    base_dir = manifest_path.parent

    print(f"Verifying {len(manifest)} artifacts against {manifest_path}...\n")
    for filename, expected_hash in sorted(manifest.items()):
        file_path = base_dir / filename
        if not file_path.exists():
            print(f"FAIL: File missing: {file_path}")
            all_matched = False
            continue

        actual_hash = compute_sha256(file_path)
        if actual_hash == expected_hash:
            print(f"OK   [{filename}] -> {actual_hash[:16]}...")
        else:
            print(f"FAIL [{filename}] -> Expected {expected_hash}, got {actual_hash}")
            all_matched = False

    if all_matched:
        print("\nALL ARTIFACTS VERIFIED SUCCESSFULLY (100% SHA-256 MATCH)")
        return True
    else:
        print("\nINTEGRITY AUDIT FAILED (HASH MISMATCH DETECTED)")
        return False

if __name__ == "__main__":
    success = verify_manifest()
    sys.exit(0 if success else 1)
