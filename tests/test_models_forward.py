from __future__ import annotations

import torch

from src.models.bigru import FlatBiGRU
from src.models.hierarchical_transformer import HierarchicalDiffTransformer
from src.models.mlp import BagOfTokensMLP


def test_models_forward_pass() -> None:
    batch_size = 2
    vocab_size = 32
    pad_id = 0

    flat_token_ids = torch.tensor([[1, 2, 3, 0], [4, 5, 0, 0]])
    flat_mask = flat_token_ids != pad_id

    mlp = BagOfTokensMLP(
        vocab_size=vocab_size,
        embedding_dim=8,
        hidden_dim=16,
        dropout=0.1,
        num_intent_classes=4,
        pad_id=pad_id,
    )
    mlp_out = mlp(token_ids=flat_token_ids, attention_mask=flat_mask)
    assert mlp_out["intent_logits"].shape == (batch_size, 4)
    assert mlp_out["hole_logits"].shape == (batch_size, 2)

    bigru = FlatBiGRU(
        vocab_size=vocab_size,
        embedding_dim=8,
        hidden_dim=8,
        num_layers=1,
        dropout=0.1,
        num_intent_classes=4,
        pad_id=pad_id,
    )
    bigru_out = bigru(token_ids=flat_token_ids, attention_mask=flat_mask)
    assert bigru_out["intent_logits"].shape == (batch_size, 4)
    assert bigru_out["hole_logits"].shape == (batch_size, 2)

    line_token_ids = torch.tensor(
        [
            [[1, 2, 0], [3, 4, 5]],
            [[6, 7, 8], [9, 0, 0]],
        ]
    )
    line_token_mask = line_token_ids != pad_id
    line_mask = torch.tensor([[True, True], [True, True]])
    line_type_ids = torch.tensor([[0, 4], [0, 2]])

    hierarchical = HierarchicalDiffTransformer(
        vocab_size=vocab_size,
        pad_id=pad_id,
        num_intent_classes=4,
        token_embedding_dim=8,
        line_type_embedding_dim=4,
        line_hidden_dim=8,
        transformer_layers=1,
        transformer_heads=2,
        transformer_ff_dim=32,
        dropout=0.1,
        max_tokens_per_line=3,
        max_lines_per_diff=2,
        use_line_type_embeddings=True,
    )
    hierarchical_out = hierarchical(
        line_token_ids=line_token_ids,
        line_token_mask=line_token_mask,
        line_mask=line_mask,
        line_type_ids=line_type_ids,
    )
    assert hierarchical_out["intent_logits"].shape == (batch_size, 4)
    assert hierarchical_out["hole_logits"].shape == (batch_size, 2)

