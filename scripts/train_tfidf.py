from __future__ import annotations

import argparse
from pathlib import Path
import pickle
import re
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import HOLE_LABELS, INTENT_LABELS
from src.data.dataset import HOLE_TO_ID, INTENT_TO_ID
from src.training.metrics import (
    compute_hole_metrics,
    compute_intent_metrics,
    plot_confusion_matrix,
)
from src.utils.config import load_and_merge_configs, save_yaml_config
from src.utils.io import read_jsonl, write_json, write_jsonl
from src.utils.logging import configure_logging
from src.utils.seed import seed_everything


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data-config", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()


def _text_for_example(example: dict, text_source: str) -> str:
    if text_source == "message":
        return example["commit_message"]
    return example["normalized_diff"]


def _setting_name(run_name: str) -> str:
    return re.sub(r"_seed\d+$", "", run_name)


def _save_predictions(
    output_path: Path,
    examples: list[dict],
    intent_pred: list[int],
    hole_pred: list[int],
    intent_prob,
    hole_prob,
) -> None:
    rows = []
    for example, pred_intent, pred_hole, probs_intent, probs_hole in zip(
        examples, intent_pred, hole_pred, intent_prob, hole_prob
    ):
        rows.append(
            {
                "example_id": example["example_id"],
                "commit_hash": example["commit_hash"],
                "file_path": example["file_path"],
                "pair_id": example["pair_id"],
                "true_intent": INTENT_TO_ID[example["intent_label"]],
                "pred_intent": int(pred_intent),
                "true_hole": HOLE_TO_ID[example["hole_label"]],
                "pred_hole": int(pred_hole),
                "intent_probs": [float(value) for value in probs_intent],
                "hole_probs": [float(value) for value in probs_hole],
            }
        )
    write_jsonl(output_path, rows)


def main() -> None:
    args = _parse_args()
    config = load_and_merge_configs(args.data_config, args.config)
    seed_everything(args.seed)
    logger = configure_logging(ROOT / "outputs" / "logs" / f"{args.run_name}.log")

    train_examples = read_jsonl(ROOT / config["paths"]["train_split"])
    val_examples = read_jsonl(ROOT / config["paths"]["val_split"])
    test_examples = read_jsonl(ROOT / config["paths"]["test_split"])

    text_source = config["text_source"]
    train_texts = [_text_for_example(example, text_source) for example in train_examples]
    val_texts = [_text_for_example(example, text_source) for example in val_examples]
    test_texts = [_text_for_example(example, text_source) for example in test_examples]

    logger.info("run_name=%s", args.run_name)
    logger.info("text_source=%s", text_source)
    logger.info("train_examples=%s val_examples=%s test_examples=%s", len(train_examples), len(val_examples), len(test_examples))

    vectorizer = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=tuple(config["vectorizer"]["word_ngram_range"]),
                    max_features=config["vectorizer"]["word_max_features"],
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=tuple(config["vectorizer"]["char_ngram_range"]),
                    max_features=config["vectorizer"]["char_max_features"],
                ),
            ),
        ]
    )

    x_train = vectorizer.fit_transform(train_texts)
    x_val = vectorizer.transform(val_texts)
    x_test = vectorizer.transform(test_texts)

    y_train_intent = [INTENT_TO_ID[example["intent_label"]] for example in train_examples]
    y_val_intent = [INTENT_TO_ID[example["intent_label"]] for example in val_examples]
    y_test_intent = [INTENT_TO_ID[example["intent_label"]] for example in test_examples]
    y_train_hole = [HOLE_TO_ID[example["hole_label"]] for example in train_examples]
    y_val_hole = [HOLE_TO_ID[example["hole_label"]] for example in val_examples]
    y_test_hole = [HOLE_TO_ID[example["hole_label"]] for example in test_examples]

    intent_clf = LogisticRegression(
        max_iter=config["classifier"]["max_iter"],
        class_weight=config["classifier"]["class_weight"],
        random_state=args.seed,
    )
    hole_clf = LogisticRegression(
        max_iter=config["classifier"]["max_iter"],
        class_weight=config["classifier"]["class_weight"],
        random_state=args.seed,
    )
    intent_clf.fit(x_train, y_train_intent)
    hole_clf.fit(x_train, y_train_hole)

    save_yaml_config(
        {
            **config,
            "runtime": {"run_name": args.run_name, "seed": args.seed},
        },
        ROOT / "outputs" / "checkpoints" / f"{args.run_name}_config.yaml",
    )
    with (ROOT / "outputs" / "checkpoints" / f"{args.run_name}.pkl").open("wb") as handle:
        pickle.dump(
            {"vectorizer": vectorizer, "intent_clf": intent_clf, "hole_clf": hole_clf},
            handle,
        )

    for split_name, matrix, examples, y_true_intent, y_true_hole in [
        ("train", x_train, train_examples, y_train_intent, y_train_hole),
        ("val", x_val, val_examples, y_val_intent, y_val_hole),
        ("test", x_test, test_examples, y_test_intent, y_test_hole),
    ]:
        intent_pred = intent_clf.predict(matrix).tolist()
        hole_pred = hole_clf.predict(matrix).tolist()
        intent_prob = intent_clf.predict_proba(matrix).tolist()
        hole_prob = hole_clf.predict_proba(matrix).tolist()

        metrics = {
            "intent": compute_intent_metrics(y_true_intent, intent_pred, INTENT_LABELS),
            "hole": compute_hole_metrics(
                y_true_hole,
                hole_pred,
                [row[1] for row in hole_prob],
            ),
        }
        write_json(
            ROOT / "outputs" / "metrics" / f"{args.run_name}_{split_name}_metrics.json",
            metrics,
        )
        _save_predictions(
            ROOT / "outputs" / "predictions" / f"{args.run_name}_{split_name}_predictions.jsonl",
            examples,
            intent_pred,
            hole_pred,
            intent_prob,
            hole_prob,
        )

        if split_name == "test":
            plot_confusion_matrix(
                matrix=metrics["intent"]["confusion_matrix"],
                labels=INTENT_LABELS,
                path=ROOT / "outputs" / "figures" / f"{args.run_name}_intent_confusion_matrix.png",
                title=f"{args.run_name} Intent Confusion Matrix",
            )
            plot_confusion_matrix(
                matrix=metrics["hole"]["confusion_matrix"],
                labels=HOLE_LABELS,
                path=ROOT / "outputs" / "figures" / f"{args.run_name}_hole_confusion_matrix.png",
                title=f"{args.run_name} Hole Confusion Matrix",
            )


if __name__ == "__main__":
    main()
