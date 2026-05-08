from __future__ import annotations

from typing import Any

import torch
import torch.nn.functional as F


def compute_multitask_loss(
    outputs: dict[str, torch.Tensor],
    intent_labels: torch.Tensor,
    hole_labels: torch.Tensor,
    lambda_hole: float = 1.0,
    task_mode: str = "multitask",
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Compute multitask or single-task loss."""

    intent_loss = F.cross_entropy(outputs["intent_logits"], intent_labels)
    hole_loss = F.cross_entropy(outputs["hole_logits"], hole_labels)

    if task_mode == "intent_only":
        total_loss = intent_loss
    elif task_mode == "hole_only":
        total_loss = lambda_hole * hole_loss
    else:
        total_loss = intent_loss + lambda_hole * hole_loss

    return total_loss, {
        "intent_loss": float(intent_loss.detach().cpu()),
        "hole_loss": float(hole_loss.detach().cpu()),
        "total_loss": float(total_loss.detach().cpu()),
    }

