# SPDX-License-Identifier: FSL-1.1-ALv2
# === MODULE_BUILD ===
# id: uchc_installed_package
#   module_name: verify_installed_package
#   module_kind: verification-tool
#   summary: verify installed runtime completeness and packaged-resource usability
#   owner: The-Interdependency/uchc
#   public_surface: source_manifest, verify, CLI
#   storage_boundary: source manifest write or installed package reads
#   network_boundary: none
#   user_data_boundary: public project source only
#   tests: package-completeness workflow in separate wheel and source-archive environments
#   rollout: required packaging gate before publication
#   rollback: retain historical candidate artifacts
#   unresolved: public distribution-path verification remains separate
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: uchc_installed_package_complete
#   given: an exact source manifest and clean installed distribution
#   then: require the complete runtime inventory, source and RECORD digests, local imports and usable packaged resources
# id: uchc_packaging_not_ratification
#   given: successful imports and fixture loading
#   then: report packaging evidence only, without mathematical or semantic promotion
# === END CONTRACTS ===
"""Run with clean installed Python -I, outside either source checkout.

Checks every runtime Python/data file against a source manifest, package RECORD,
and the interpreter's install prefix. Exercises packaged EDCM fixture loading and
label replacement. This is a packaging gate, not mathematical ratification.
"""
import argparse
import base64
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tomllib


def source_manifest(root: Path) -> dict:
    project = tomllib.loads((root / "pyproject.toml").read_text())
    files = {}
    for package, location in project["tool"]["setuptools"]["package-dir"].items():
        for path in (root / location).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".json") and "__pycache__" not in path.parts:
                name = package.replace(".", "/") + "/" + path.relative_to(root / location).as_posix()
                files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"version": project["project"]["version"], "files": dict(sorted(files.items()))}


def verify(manifest: Path) -> dict:
    expected = json.loads(manifest.read_text())
    distribution = importlib.metadata.distribution("uchc")
    if distribution.version != expected["version"]:
        raise ValueError("installed UCHC version mismatch")
    entries = {str(entry): entry for entry in distribution.files or ()}
    if not entries:
        raise ValueError("installed package has no file inventory")
    runtime = {name for name in entries if name.endswith((".py", ".json")) and ".dist-info/" not in name}
    if runtime != set(expected["files"]):
        raise ValueError("installed runtime inventory differs from source manifest")
    checked = []
    for name, digest in expected["files"].items():
        entry = entries.get(name)
        if entry is None or entry.hash is None or entry.hash.mode != "sha256":
            raise ValueError("file missing from wheel RECORD: " + name)
        path = Path(distribution.locate_file(entry)).resolve()
        if not path.is_relative_to(Path(sys.prefix).resolve()):
            raise ValueError("package is not installed in this environment: " + name)
        actual = hashlib.sha256(path.read_bytes()).digest()
        if actual.hex() != digest or base64.urlsafe_b64encode(actual).rstrip(b"=").decode() != entry.hash.value:
            raise ValueError("installed file digest mismatch: " + name)
        if name.endswith(".py") and not name.endswith("/__main__.py"):
            module_name = name[:-3].replace("/", ".").removesuffix(".__init__")
            module = importlib.import_module(module_name)
            if Path(module.__file__).resolve() != path:
                raise ValueError("import was shadowed: " + module_name)
        checked.append(name)
    from english_gonol.edcm_metric_origins import load_metric_origin_specs
    from uchc_polyglot import PolyglotReferent, attach_label, build_label_attachment, same_referent
    fixture = load_metric_origin_specs()
    if fixture["producer_commit"] != "0873c105799681ea1f7ccb3e619d1f7aebbd85e0":
        raise ValueError("metric-origin producer mismatch")
    before = PolyglotReferent(ucns_identity_sha256="a" * 64)
    after = attach_label(before, build_label_attachment(
        ucns_identity_sha256=before.referent_identity, language_tag="es",
        surface="cardíaco", scope="technical", source_id="packaging:smoke"))
    if not same_referent(before, after):
        raise ValueError("label attachment changed referent identity")
    return {"version": distribution.version, "files": len(checked),
            "status": "passed", "source_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path, help="write a source manifest instead of checking an installation")
    args = parser.parse_args()
    if args.source:
        args.manifest.write_text(json.dumps(source_manifest(args.source), indent=2) + "\n")
    else:
        print(json.dumps(verify(args.manifest), sort_keys=True))
