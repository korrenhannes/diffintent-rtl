from __future__ import annotations

from src.data.diff_parser import normalize_diff, parse_unified_diff


def test_diff_parser_converts_unified_diff_to_typed_lines() -> None:
    unified_diff = """diff --git a/foo.sv b/foo.sv
index 111..222 100644
--- a/foo.sv
+++ b/foo.sv
@@ -1,3 +1,4 @@
 module foo;
-  assign a = 1'b0;
+  assign a = 1'b1;
+  logic valid_q;
 endmodule
"""
    typed_lines = parse_unified_diff(unified_diff, "hw/ip/foo/rtl/foo.sv")
    assert typed_lines[0]["type"] == "FILE"
    assert any(line["type"] == "HUNK" for line in typed_lines)
    assert any(line["type"] == "DEL" for line in typed_lines)
    assert any(line["type"] == "ADD" for line in typed_lines)

    normalized_lines, normalized_text = normalize_diff(
        unified_diff=unified_diff,
        file_path="hw/ip/foo/rtl/foo.sv",
        max_lines_per_diff=16,
        keep_context_lines=True,
    )
    assert normalized_lines
    assert "<ADD>" in normalized_text
    assert "<DEL>" in normalized_text

