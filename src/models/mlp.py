from __future__ import annotations

import torch
from torch import nn

from src.models.heads import MultiTaskHeads


class BagOfTokensMLP(nn.Module):
    """Embedding + mean pooling + MLP for flat token inputs."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        dropout: float,
        num_intent_classes: int,
        pad_id: int,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
        self.dropout = nn.Dropout(dropout)
        self.encoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.heads = MultiTaskHeads(
            input_dim=hidden_dim,
            num_intent_classes=num_intent_classes,
            dropout=dropout,
        )

    def forward(
        self,
        token_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        **_: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        embedded = self.embedding(token_ids)
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (embedded * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        encoded = self.encoder(self.dropout(pooled))
        return self.heads(encoded)

