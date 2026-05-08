from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from src.models.heads import MultiTaskHeads


class AttentionPooling(nn.Module):
    """Attention pooling over sequence states."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.score = nn.Linear(input_dim, 1)

    def forward(self, states: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        scores = self.score(states).squeeze(-1)
        scores = scores.masked_fill(~mask, float("-inf"))
        weights = torch.softmax(scores, dim=-1)
        weights = torch.nan_to_num(weights, nan=0.0)
        return torch.einsum("bs,bsh->bh", weights, states)


class FlatBiGRU(nn.Module):
    """Flat token-sequence BiGRU with attention pooling."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_layers: int,
        dropout: float,
        num_intent_classes: int,
        pad_id: int,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
        self.gru = nn.GRU(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.pool = AttentionPooling(hidden_dim * 2)
        self.heads = MultiTaskHeads(
            input_dim=hidden_dim * 2,
            num_intent_classes=num_intent_classes,
            dropout=dropout,
        )

    def forward(
        self,
        token_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        **_: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        lengths = attention_mask.sum(dim=1).cpu()
        embedded = self.embedding(token_ids)
        packed = pack_padded_sequence(
            embedded,
            lengths=lengths,
            batch_first=True,
            enforce_sorted=False,
        )
        packed_outputs, _ = self.gru(packed)
        outputs, _ = pad_packed_sequence(
            packed_outputs,
            batch_first=True,
            total_length=token_ids.size(1),
        )
        pooled = self.pool(outputs, attention_mask)
        return self.heads(self.dropout(pooled))

