"""Frozen primitive-layer run: character definitions + corrected suffixiation.

Builds the complete character-definition layer and two replayable suffixiation
receipts (``try + ing`` preserving y, ``try + ed`` resolving y-to-i) as the
frozen evidence for the corrected construction contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from english_gonol.gonol import construct_gonol
from english_gonol.language.character_definitions import (
    build_character_definition_layer,
    character_layer_record,
)
from english_gonol.language.suffixiation import suffixiate


def run_payload() -> dict:
    layer = build_character_definition_layer()
    base = construct_gonol(scale="word", source="try", source_id="primitive:try")
    ing = construct_gonol(
        scale="suffix",
        source="ing",
        source_id="primitive:ing",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    ed = construct_gonol(
        scale="suffix",
        source="ed",
        source_id="primitive:ed",
        carried_options=(("suffix-coupling.vowel-initial", "true"),),
    )
    trying = suffixiate(base.gonol, ing.gonol, source_id="primitive:trying", layer=layer)
    tried = suffixiate(base.gonol, ed.gonol, source_id="primitive:tried", layer=layer)
    return {
        "schema": "english-gonol.primitive-layer",
        "version": "v0",
        "character_layer": character_layer_record(layer),
        "suffixiation": [trying.record(), tried.record()],
        "nonclaims": [
            "no global morphology law recreates y behavior",
            "no character definition is selected canon",
            "numerology definitions are candidate evidence, not canon",
        ],
        "hmmm": [
            "y would like its belongings returned by ing; this run returns them to the y character definition-space",
            "exact UCNS affixiation geometry remains unresolved",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    payload = run_payload()
    Path(args.out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
