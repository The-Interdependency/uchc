# ratios: loc_comments=12:10 imports_exports=4:1 calls_definitions=3:1
# === CHECKS ===
# id: check_unicode_verification_refuses_optimization
#   proves: uchc_unicode_verification_not_optimized
#   call: self::test_unicode_extraction_refuses_optimized_python
#   requires: pytest
#   timeout: 60
#   mutates: none
#   cleanup: subprocess_exit
# === END CHECKS ===
"""The verifier must refuse before assertions can be disabled."""
import os
from pathlib import Path
import subprocess
import sys


def test_unicode_extraction_refuses_optimized_python():
    root = Path(__file__).resolve().parents[1]
    for flags, optimization in ((['-O'], ''), ([], '1')):
        env = dict(os.environ, PYTHONPATH=str(root / 'human/english'), PYTHONOPTIMIZE=optimization)
        result = subprocess.run([sys.executable, *flags, str(root / 'tools/verify_unicode_extraction.py'), 'missing'],
                                env=env, capture_output=True, text=True)
        assert result.returncode != 0 and not result.stdout
        assert 'OPTIMIZED_VERIFICATION_FORBIDDEN' in result.stderr
# ratios: loc_comments=12:10 imports_exports=4:1 calls_definitions=3:1
