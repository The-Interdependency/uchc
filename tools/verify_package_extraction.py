# SPDX-License-Identifier: FSL-1.1-ALv2
# === MODULE_BUILD ===
# id: uchc_package_extraction
#   module_name: verify_package_extraction
#   module_kind: verification-tool
#   summary: verify the complete runtime migration against exact forge Git objects
#   owner: The-Interdependency/uchc
#   public_surface: verify, CLI
#   storage_boundary: read-only Git objects and declared extraction files
#   network_boundary: none
#   user_data_boundary: public project source only
#   tests: package-completeness workflow; source inventory and digest verification
#   rollout: required package provenance gate
#   rollback: retain historical candidate identities
#   unresolved: release and scoped authority transition
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_package_extraction_complete
#   given: exact forge Git source and declared extraction inventory
#   then: reject missing runtime files, changed source bytes or unrecorded adaptations
# id: uchc_package_extraction_no_authority_transfer
#   given: matching source and target files
#   then: provenance verification grants no implementation or domain authority
# === END CONTRACTS ===
"""Verify the complete declared Stack runtime extraction without executing it.

Usage: python tools/verify_package_extraction.py /path/to/stack
Reads exact Git objects, so the forge may be checked out at a later commit.
This proves byte provenance only; it does not transfer domain authority.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def verify(forge: Path, root: Path) -> dict:
    record = json.loads((root / "docs/package-extraction.json").read_text())
    commit = record["source_commit"]
    paths = subprocess.check_output(
        ["git", "-C", str(forge), "ls-tree", "-r", "--name-only", commit,
         "research/english-gonol/english_gonol", "research/python-gonol/python_gonol"],
        text=True,
    ).splitlines()
    runtime = {p for p in paths if p.endswith((".py", ".json"))}
    declared = {item["source"] for item in record["files"] if item["kind"] == "runtime"}
    excluded = set(record["forge_only"])
    if runtime != declared | excluded or declared & excluded:
        raise ValueError("runtime extraction inventory is incomplete or overlapping")
    for item in record["files"]:
        original = subprocess.check_output(
            ["git", "-C", str(forge), "show", commit + ":" + item["source"]]
        )
        target = (root / item["target"]).read_bytes()
        if hashlib.sha256(original).hexdigest() != item["source_sha256"]:
            raise ValueError("producer digest mismatch: " + item["source"])
        if hashlib.sha256(target).hexdigest() != item["target_sha256"]:
            raise ValueError("extracted digest mismatch: " + item["target"])
        if item["adaptation"] is None and original != target:
            raise ValueError("unrecorded extraction change: " + item["target"])
    if record["authority_transfer"] is not False:
        raise ValueError("extraction cannot transfer authority")
    return {"source_commit": commit, "files": len(record["files"]),
            "runtime_files": len(declared), "forge_only": len(excluded),
            "standing": "exact extraction; graduation gates remain separate"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("forge", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.forge, Path(__file__).resolve().parents[1]), sort_keys=True))
