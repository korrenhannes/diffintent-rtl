from __future__ import annotations

import torch
from torch import nn


class MultiTaskHeads(nn.Module):
    """Shared heads for intent and hole classification."""

    def __init__(self, input_dim: int, num_intent_classes: int, dropout: float) -> None:
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.intent_head = nn.Linear(input_dim, num_intent_classes)
        self.hole_head = nn.Linear(input_dim, 2)

    def forward(self, features: torch.Tensor) -> dict[str, torch.Tensor]:
        hidden = self.dropout(features)
        return {
            "intent_logits": self.intent_head(hidden),
            "hole_logits": self.hole_head(hidden),
        }

