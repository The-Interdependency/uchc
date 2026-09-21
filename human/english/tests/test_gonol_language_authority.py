from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_SURFACES = (
    ROOT / "README.md",
    ROOT / "docs" / "GONOL_LANGUAGE_BOUNDARY.md",
)


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_live_surfaces_route_gonol_authority_consistently() -> None:
    boundary = _compact(ROOT / "docs" / "GONOL_LANGUAGE_BOUNDARY.md")
    readme = _compact(ROOT / "README.md")

    for text in (boundary, readme):
        assert "every admitted character is a gonol" in text
        assert "METAPAT" in text
        assert "UCNS" in text
        assert "EDCM" in text

    assert "METAPAT defines affixiation" in boundary
    assert "UCNS owns any exact geometric realization" in boundary
    assert "English Gonol Construction applies affixiation to text-domain gonols" in boundary
    assert "scale option sets" in boundary
    assert "edcm.gonol" in boundary
    assert "Once closed, a gonol is atomic at any scale" in boundary
    assert "one exact scalar -> one shared character identity" in readme
    assert "one exact surface -> one shared word identity" in readme
    assert "Once closed, a gonol is atomic at an admissible consuming scale" in readme
    assert "mandatory adjacent-scale ladder" in boundary
    assert "Closed gonols may participate directly at any admissible scale" in boundary
    assert "does not mutate `sys.path`" in boundary


def test_live_surfaces_do_not_restore_ucns_language_ownership() -> None:
    forbidden = (
        "UCNS owns the gonol construction",
        "UCNS lexical construction remains upstream",
        "UCNS owns lexical/gonol construction surfaces",
        "English Gonol owns neither lexical-floor membership nor UCNS character-, word-, or definition-gonol construction",
        "UCNS has authorized a Scrabble dictionary as the replacement lexical source class",
    )
    for path in LIVE_SURFACES:
        text = _compact(path)
        for phrase in forbidden:
            assert phrase not in text, f"stale authority in {path.relative_to(ROOT)}: {phrase}"


def test_unresolved_ucns_operations_remain_hmmm_not_semantics() -> None:
    boundary = _compact(ROOT / "docs" / "GONOL_LANGUAGE_BOUNDARY.md")
    assert "Unicode names, dictionary definitions" in boundary
    assert "An unresolved operation remains `hmmm`" in boundary
    assert "invented carrier" in boundary


def test_measurement_does_not_activate_from_construction() -> None:
    readme = _compact(ROOT / "README.md")
    boundary = _compact(ROOT / "docs" / "GONOL_LANGUAGE_BOUNDARY.md")
    assert "English Gonol construction does not validate EDCM measurement" in boundary
    assert "EDCM -> measurement/evaluation only" in readme
