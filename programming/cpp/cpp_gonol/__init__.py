# ratios: loc_comments=2:1 imports_exports=1:1 calls_definitions=0:0
"""Construct C++23 UTF-8 source with construct(data, source_id=...) and replay(record)."""
from .source import construct, phase2_text, replay

__all__ = ["construct", "phase2_text", "replay"]
# ratios: loc_comments=2:1 imports_exports=1:1 calls_definitions=0:0
