# ratios: loc_comments=13:13 imports_exports=4:1 calls_definitions=3:1
# SPDX-License-Identifier: FSL-1.1-ALv2
# Copyright 2026 Erin Spencer
# === CHECKS ===
# id: check_attachment_extraction_refuses_optimized_python
#   proves: uchc_attachment_verification_not_optimized
#   call: self::test_extraction_refuses_optimized_python
#   mutates: none
#   cleanup: subprocess_exit
# === END CHECKS ===
"""Usage: PYTHONPATH=human/english pytest -c /dev/null tests/test_attachment_verification.py.

GPT generated; context, prompt Erin Spencer.
This tests the verifier refusal, not corpus construction or authority graduation.
"""
from pathlib import Path
import os
import subprocess
import sys


def test_extraction_refuses_optimized_python():
    root = Path(__file__).resolve().parents[1]
    script = root / 'tools/verify_attachment_extraction.py'
    for flags, optimization in ((['-O'], ''), ([], '1')):
        env = dict(os.environ, PYTHONPATH=str(root / 'human/english'), PYTHONOPTIMIZE=optimization)
        result = subprocess.run([sys.executable, *flags, str(script), 'not-a-forge'],
                                env=env, capture_output=True, text=True)
        assert result.returncode != 0 and not result.stdout
        assert 'OPTIMIZED_VERIFICATION_FORBIDDEN' in result.stderr
# ratios: loc_comments=13:13 imports_exports=4:1 calls_definitions=3:1
