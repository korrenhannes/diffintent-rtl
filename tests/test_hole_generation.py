from __future__ import annotations

from src.data.hole_generation import generate_synthetic_hole


def test_hole_generation_returns_valid_mutation() -> None:
    example = {
        "commit_hash": "abc123",
        "file_path": "hw/ip/foo/rtl/foo.sv",
        "commit_message": "fix reset logic",
        "pair_id": "abc123::hw/ip/foo/rtl/foo.sv",
        "example_id": "abc123::hw/ip/foo/rtl/foo.sv::real",
        "intent_label": "bug_fix",
        "hole_label": "complete",
        "old_code": "always_ff @(posedge clk_i) begin\n  if (!rst_ni) valid_q <= 1'b1;\nend\n",
        "new_code": "always_ff @(posedge clk_i) begin\n  if (!rst_ni) valid_q <= 1'b0;\nend\n",
        "typed_lines": [
            {"type": "FILE", "text": "hw/ip/foo/rtl/foo.sv", "hunk_id": -1},
            {"type": "HUNK", "text": "@@ -1,2 +1,2 @@", "hunk_id": 0},
            {"type": "CTX", "text": "always_ff @(posedge clk_i) begin", "hunk_id": 0},
            {"type": "ADD", "text": "  if (!rst_ni) valid_q <= 1'b0;", "hunk_id": 0},
            {"type": "DEL", "text": "  if (!rst_ni) valid_q <= 1'b1;", "hunk_id": 0},
            {"type": "CTX", "text": "end", "hunk_id": 0},
        ],
        "normalized_diff": "",
    }
    synthetic = generate_synthetic_hole(example)
    assert synthetic is not None
    assert synthetic["hole_label"] == "synthetic_hole"
    assert synthetic["mutation_type"] != "none"
    assert synthetic["normalized_diff"].strip()

