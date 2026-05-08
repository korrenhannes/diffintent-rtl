from __future__ import annotations

from src.data.tokenizer import tokenize_sv_text


def test_tokenizer_handles_systemverilog_tokens() -> None:
    tokens = tokenize_sv_text("always_ff @(posedge clk_i) if (!rst_ni) valid_q <= 1'b0;")
    assert "always_ff" in tokens
    assert "posedge" in tokens
    assert "<=" in tokens
    assert "1'b0" in tokens
    assert ";" in tokens

