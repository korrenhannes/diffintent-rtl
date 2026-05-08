from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import torch
from torch import nn
from torch.utils.data import DataLoader

from src.training.losses import compute_multitask_loss
from src.training.metrics import (
    compute_hole_metrics,
    compute_intent_metrics,
    plot_confusion_matrix,
)
from src.utils.io import ensure_dir, write_json, write_jsonl


@dataclass
class TrainerConfig:
    epochs: int
    learning_rate: float
    weight_decay: float
    lambda_hole: float
    task_mode: str
    early_stopping_patience: int
    run_name: str
    checkpoint_dir: Path
    metrics_dir: Path
    predictions_dir: Path
    figures_dir: Path
    log_history_path: Path


class Trainer:
    """Generic trainer for multitask neural models."""

    def __init__(
        self,
        model: nn.Module,
        device: torch.device,
        optimizer: torch.optim.Optimizer,
        config: TrainerConfig,
    ) -> None:
        self.model = model
        self.device = device
        self.optimizer = optimizer
        self.config = config

    def _move_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.to(self.device) if isinstance(value, torch.Tensor) else value
            for key, value in batch.items()
        }

    def _forward_batch(
        self,
        batch: dict[str, Any],
        compute_loss: bool = True,
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor | None, dict[str, Any] | None]:
        inputs = {
            key: value
            for key, value in batch.items()
            if key
            not in {
                "intent_labels",
                "hole_labels",
                "metadata",
            }
        }
        outputs = self.model(**inputs)
        if not compute_loss:
            return outputs, None, None
        loss, loss_info = compute_multitask_loss(
            outputs=outputs,
            intent_labels=batch["intent_labels"],
            hole_labels=batch["hole_labels"],
            lambda_hole=self.config.lambda_hole,
            task_mode=self.config.task_mode,
        )
        return outputs, loss, loss_info

    def _run_epoch(self, loader: DataLoader, training: bool) -> dict[str, float]:
        self.model.train(training)
        total_loss = 0.0
        total_batches = 0

        for batch in loader:
            batch = self._move_batch(batch)
            if training:
                self.optimizer.zero_grad(set_to_none=True)
            _, loss, _ = self._forward_batch(batch, compute_loss=True)
            if training:
                assert loss is not None
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()

            assert loss is not None
            total_loss += float(loss.detach().cpu())
            total_batches += 1

        return {
            "loss": total_loss / max(total_batches, 1),
        }

    @torch.no_grad()
    def predict(
        self,
        loader: DataLoader,
        return_loss: bool = False,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], float | None]:
        self.model.eval()
        all_intent_true: list[int] = []
        all_intent_pred: list[int] = []
        all_hole_true: list[int] = []
        all_hole_pred: list[int] = []
        all_hole_prob: list[float] = []
        prediction_rows: list[dict[str, Any]] = []
        total_loss = 0.0
        total_batches = 0

        for batch in loader:
            metadata = batch["metadata"]
            batch = self._move_batch(batch)
            outputs, loss, _ = self._forward_batch(batch, compute_loss=return_loss)
            if return_loss:
                assert loss is not None
                total_loss += float(loss.detach().cpu())
                total_batches += 1
            intent_probs = torch.softmax(outputs["intent_logits"], dim=-1)
            hole_probs = torch.softmax(outputs["hole_logits"], dim=-1)
            intent_pred = intent_probs.argmax(dim=-1).cpu().tolist()
            hole_pred = hole_probs.argmax(dim=-1).cpu().tolist()
            hole_prob = hole_probs[:, 1].cpu().tolist()
            intent_true = batch["intent_labels"].cpu().tolist()
            hole_true = batch["hole_labels"].cpu().tolist()

            all_intent_true.extend(intent_true)
            all_intent_pred.extend(intent_pred)
            all_hole_true.extend(hole_true)
            all_hole_pred.extend(hole_pred)
            all_hole_prob.extend(hole_prob)

            for item, intent_label, hole_label, intent_distribution, hole_distribution in zip(
                metadata,
                intent_pred,
                hole_pred,
                intent_probs.cpu().tolist(),
                hole_probs.cpu().tolist(),
            ):
                prediction_rows.append(
                    {
                        "example_id": item["example_id"],
                        "commit_hash": item["commit_hash"],
                        "file_path": item["file_path"],
                        "pair_id": item["pair_id"],
                        "true_intent": int(item["intent_label"]),
                        "pred_intent": int(intent_label),
                        "true_hole": int(item["hole_label"]),
                        "pred_hole": int(hole_label),
                        "intent_probs": [float(value) for value in intent_distribution],
                        "hole_probs": [float(value) for value in hole_distribution],
                    }
                )

        metrics = {
            "intent": compute_intent_metrics(all_intent_true, all_intent_pred),
            "hole": compute_hole_metrics(all_hole_true, all_hole_pred, all_hole_prob),
        }
        avg_loss = total_loss / max(total_batches, 1) if return_loss else None
        return metrics, prediction_rows, avg_loss

    def _primary_metric(self, metrics: dict[str, Any]) -> float:
        if self.config.task_mode == "intent_only":
            return float(metrics["intent"]["macro_f1"])
        if self.config.task_mode == "hole_only":
            return float(metrics["hole"]["f1"])
        return float(metrics["intent"]["macro_f1"]) + float(metrics["hole"]["f1"])

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        test_loader: DataLoader,
    ) -> dict[str, Any]:
        ensure_dir(self.config.checkpoint_dir)
        ensure_dir(self.config.metrics_dir)
        ensure_dir(self.config.predictions_dir)
        ensure_dir(self.config.figures_dir)

        best_score = -float("inf")
        best_state: dict[str, Any] | None = None
        history: list[dict[str, Any]] = []
        patience = 0

        for epoch in range(1, self.config.epochs + 1):
            train_stats = self._run_epoch(train_loader, training=True)
            val_metrics, _, val_loss = self.predict(val_loader, return_loss=True)
            score = self._primary_metric(val_metrics)

            epoch_record = {
                "epoch": epoch,
                "train_loss": train_stats["loss"],
                "val_loss": val_loss,
                "val_intent_macro_f1": val_metrics["intent"]["macro_f1"],
                "val_hole_f1": val_metrics["hole"]["f1"],
                "selection_score": score,
            }
            history.append(epoch_record)
            print(
                f"[{self.config.run_name}] "
                f"epoch={epoch} "
                f"train_loss={train_stats['loss']:.4f} "
                f"val_loss={val_loss:.4f} "
                f"val_intent_macro_f1={val_metrics['intent']['macro_f1']:.4f} "
                f"val_hole_f1={val_metrics['hole']['f1']:.4f} "
                f"score={score:.4f}",
                flush=True,
            )

            if score > best_score:
                best_score = score
                best_state = {
                    "model_state_dict": self.model.state_dict(),
                    "epoch": epoch,
                    "score": score,
                }
                torch.save(
                    best_state,
                    self.config.checkpoint_dir / f"{self.config.run_name}.pt",
                )
                patience = 0
            else:
                patience += 1
                if patience >= self.config.early_stopping_patience:
                    break

        write_json(self.config.log_history_path, {"history": history})

        if best_state is None:
            raise RuntimeError("Training did not produce a checkpoint.")
        self.model.load_state_dict(best_state["model_state_dict"])

        outputs: dict[str, Any] = {"history": history}
        for split_name, loader in [
            ("train", train_loader),
            ("val", val_loader),
            ("test", test_loader),
        ]:
            metrics, predictions, _ = self.predict(loader)
            write_json(
                self.config.metrics_dir
                / f"{self.config.run_name}_{split_name}_metrics.json",
                metrics,
            )
            write_jsonl(
                self.config.predictions_dir
                / f"{self.config.run_name}_{split_name}_predictions.jsonl",
                predictions,
            )
            outputs[split_name] = metrics

        plot_confusion_matrix(
            matrix=outputs["test"]["intent"]["confusion_matrix"],
            labels=outputs["test"]["intent"]["labels"],
            path=self.config.figures_dir
            / f"{self.config.run_name}_intent_confusion_matrix.png",
            title=f"{self.config.run_name} Intent Confusion Matrix",
        )
        plot_confusion_matrix(
            matrix=outputs["test"]["hole"]["confusion_matrix"],
            labels=outputs["test"]["hole"]["labels"],
            path=self.config.figures_dir
            / f"{self.config.run_name}_hole_confusion_matrix.png",
            title=f"{self.config.run_name} Hole Confusion Matrix",
        )
        return outputs
