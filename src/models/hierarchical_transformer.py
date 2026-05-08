from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from src.models.heads import MultiTaskHeads


class LineAttentionPooling(nn.Module):
    """Attention pooling over line states."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.score = nn.Linear(input_dim, 1)

    def forward(self, states: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        scores = self.score(states).squeeze(-1)
        scores = scores.masked_fill(~mask, float("-inf"))
        weights = torch.softmax(scores, dim=-1)
        weights = torch.nan_to_num(weights, nan=0.0)
        return torch.einsum("bl,blh->bh", weights, states)


class HierarchicalDiffTransformer(nn.Module):
    """Diff-aware hierarchical encoder with optional line-type embeddings."""

    def __init__(
        self,
        vocab_size: int,
        pad_id: int,
        num_intent_classes: int,
        token_embedding_dim: int,
        line_type_embedding_dim: int,
        line_hidden_dim: int,
        transformer_layers: int,
        transformer_heads: int,
        transformer_ff_dim: int,
        dropout: float,
        max_tokens_per_line: int,
        max_lines_per_diff: int,
        use_line_type_embeddings: bool = True,
    ) -> None:
        super().__init__()
        self.use_line_type_embeddings = use_line_type_embeddings
        self.token_embedding = nn.Embedding(
            vocab_size, token_embedding_dim, padding_idx=pad_id
        )
        self.token_position_embedding = nn.Embedding(
            max_tokens_per_line, token_embedding_dim
        )
        self.line_encoder = nn.GRU(
            input_size=token_embedding_dim,
            hidden_size=line_hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        line_repr_dim = line_hidden_dim * 2
        self.line_type_embedding = nn.Embedding(6, line_type_embedding_dim)
        projection_input_dim = (
            line_repr_dim + line_type_embedding_dim
            if use_line_type_embeddings
            else line_repr_dim
        )
        self.line_projection = nn.Linear(projection_input_dim, line_repr_dim)
        self.line_position_embedding = nn.Embedding(max_lines_per_diff, line_repr_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=line_repr_dim,
            nhead=transformer_heads,
            dim_feedforward=transformer_ff_dim,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.diff_encoder = nn.TransformerEncoder(
            encoder_layer=encoder_layer,
            num_layers=transformer_layers,
            enable_nested_tensor=False,
        )
        self.dropout = nn.Dropout(dropout)
        self.pool = LineAttentionPooling(line_repr_dim)
        self.heads = MultiTaskHeads(
            input_dim=line_repr_dim,
            num_intent_classes=num_intent_classes,
            dropout=dropout,
        )

    def _encode_lines(
        self,
        line_token_ids: torch.Tensor,
        line_token_mask: torch.Tensor,
    ) -> torch.Tensor:
        batch_size, max_lines, max_tokens = line_token_ids.shape
        flat_tokens = line_token_ids.reshape(batch_size * max_lines, max_tokens)
        flat_mask = line_token_mask.reshape(batch_size * max_lines, max_tokens)
        valid_lines = flat_mask.any(dim=1)
        output_dim = self.line_encoder.hidden_size * 2
        line_representations = torch.zeros(
            (batch_size * max_lines, output_dim),
            device=line_token_ids.device,
        )

        if valid_lines.any():
            valid_tokens = flat_tokens[valid_lines]
            valid_mask = flat_mask[valid_lines]
            lengths = valid_mask.sum(dim=1).cpu()
            positions = torch.arange(max_tokens, device=line_token_ids.device).unsqueeze(0)
            positions = positions.expand(valid_tokens.size(0), -1)
            embedded = self.token_embedding(valid_tokens) + self.token_position_embedding(
                positions
            )
            packed = pack_padded_sequence(
                embedded,
                lengths=lengths,
                batch_first=True,
                enforce_sorted=False,
            )
            packed_outputs, _ = self.line_encoder(packed)
            outputs, _ = pad_packed_sequence(
                packed_outputs,
                batch_first=True,
                total_length=max_tokens,
            )
            mask = valid_mask.unsqueeze(-1).float()
            pooled = (outputs * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
            line_representations[valid_lines] = pooled

        return line_representations.reshape(batch_size, max_lines, output_dim)

    def forward(
        self,
        line_token_ids: torch.Tensor,
        line_token_mask: torch.Tensor,
        line_mask: torch.Tensor,
        line_type_ids: torch.Tensor,
        **_: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        line_states = self._encode_lines(line_token_ids, line_token_mask)
        if self.use_line_type_embeddings:
            line_type_vectors = self.line_type_embedding(line_type_ids)
            line_states = torch.cat([line_states, line_type_vectors], dim=-1)

        line_states = self.line_projection(line_states)
        line_positions = torch.arange(
            line_states.size(1), device=line_states.device
        ).unsqueeze(0)
        line_states = line_states + self.line_position_embedding(line_positions)
        encoded = self.diff_encoder(
            self.dropout(line_states),
            src_key_padding_mask=~line_mask,
        )
        pooled = self.pool(encoded, line_mask)
        return self.heads(pooled)
