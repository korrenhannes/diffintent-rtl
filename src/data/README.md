# DiffIntent-RTL

DiffIntent-RTL is a PyTorch-based course project for understanding SystemVerilog RTL code changes from OpenTitan history. The repository builds a dataset from real commits, weakly labels change intent, generates synthetic implementation holes, and compares lexical baselines against neural diff models. The repository also includes an error-analysis study, an improved weak-labeling scheme, and a cross-project generalization experiment on a second hardware project (Caliptra).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Conda is also supported:

```bash
conda env create -f environment.yml
conda activate diffintent-rtl
```

> Note: the error-analysis and generalization studies only require `pyyaml`, `numpy`, `matplotlib`, and `scikit-learn` (no PyTorch / GPU needed).

## Data Construction

The pipeline mines modified RTL `*.sv` files (under `hw/**/rtl/` for OpenTitan and `src/**/rtl/` for Caliptra-style layouts) while excluding DV, test, vendor, third-party, generated, build, and output paths.

Dataset construction steps:

```bash
bash scripts/clone_repo.sh
python3 scripts/extract_commits.py --config configs/data_opentitan_smoke.yaml
python3 scripts/build_dataset.py --config configs/data_opentitan_smoke.yaml
python3 scripts/generate_holes.py --config configs/data_opentitan_smoke.yaml
python3 scripts/split_dataset.py --config configs/data_opentitan_smoke.yaml
```

## Smoke Run

```bash
bash scripts/run_smoke.sh
```

Smoke mode uses small mining limits and 2 training epochs for neural models so the full pipeline completes on CPU.

### Smoke Snapshot

Current saved smoke outputs were generated from:

- 45 mined raw RTL candidates from the first 100 commits examined
- 15 weak-labeled real examples
- 15 paired synthetic holes
- 30 total examples after pairing

Saved aggregate smoke results in `outputs/metrics/smoke_main_results.csv` currently show:

- `smoke_tfidf_lr`: intent macro-F1 `1.00`, hole F1 `0.5714`, hole AUROC `0.7778`
- `smoke_mlp`: intent macro-F1 `1.00`, hole F1 `0.4127`, hole AUROC `0.4815`
- `smoke_bigru`: intent macro-F1 `0.75`, hole F1 `0.3238`, hole AUROC `0.4444`
- `smoke_hierarchical_transformer`: intent macro-F1 `0.5222`, hole F1 `0.00`, hole AUROC `0.4815`

## Full Run

```bash
bash scripts/run_full_experiment.sh
```

Full mode uses the larger planned preprocessing and training limits. The completed repository run uses three seeds for the four main full models and the main `no_line_type` ablation, plus reference-seed full runs for the auxiliary ablations to keep wall-clock runtime tractable on a laptop-class machine.

### Full Snapshot

Current saved full outputs in `outputs/metrics/main_results.csv` show:

- `full_tfidf_lr`: intent macro-F1 `0.4197`, hole F1 `0.5430`, hole AUROC `0.6123`
- `full_mlp`: intent macro-F1 `0.2961`, hole F1 `0.3293`, hole AUROC `0.5488`
- `full_bigru`: intent macro-F1 `0.3023`, hole F1 `0.4204`, hole AUROC `0.5942`
- `full_hierarchical_transformer`: intent macro-F1 `0.3007`, hole F1 `0.6029`, hole AUROC `0.7352`

## Additional Studies

These studies extend the base experiment with deeper analysis, an improved labeler, and a cross-project generalization test.

### Error analysis

Produces per-class intent F1 and confusion matrices from the saved test predictions (no training or download required):

```bash
python3 scripts/error_analysis.py
```

Key finding: the macro-F1 gap is driven by the rare `refactor_cleanup` class, on which the Hierarchical Transformer collapses (F1 = 0.00), explaining why the lexical baseline outperforms the neural models on intent classification.

### Improved weak labeling

The keyword lists in `src/data/labeling.py` (`INTENT_PATTERNS`) were expanded with cross-project synonyms (e.g. `enhance`, `improve`, `update`, `resolve`). This reduced the share of commits discarded by the weak labeler from 29% to 16% on OpenTitan and from 53% to 25% on Caliptra.

### Cross-project generalization (Caliptra)

The mining path rules in `src/data/git_mining.py` were extended to also accept `src/`-style layouts, enabling mining from a second hardware project. To reproduce:

```bash
git clone --depth 300 https://github.com/lowRISC/opentitan.git external/opentitan
git clone --depth 300 https://github.com/chipsalliance/caliptra-rtl.git external/caliptra
python3 scripts/extract_commits.py --config configs/data_opentitan_smoke.yaml
python3 scripts/extract_commits.py --config configs/data_caliptra_smoke.yaml
python3 scripts/generalization_study.py
```

Key finding: the weak labeler and change-type profile do not transfer cleanly across projects — OpenTitan changes are feature-dominated while Caliptra changes are bug-fix-dominated — indicating limited generalization of a model trained on a single project.

### Hardware-aware feature model

A fifth intent model that, instead of treating the diff as raw text, extracts hardware-aware features (lines added/removed, whether the change touches reset / always_ff / parameters / assertions, signal-declaration and control-flow counts, etc.) and trains a Random Forest on them. It is compared against the lexical baseline and a hybrid (text + features) on the same split. This uses the larger `data_opentitan_medium.yaml` dataset.

```bash
python3 scripts/extract_commits.py --config configs/data_opentitan_medium.yaml
python3 scripts/build_dataset.py --config configs/data_opentitan_medium.yaml
python3 scripts/rtl_features_model.py
```

Key finding: hardware-aware features with a Random Forest reach intent macro-F1 of 0.527 versus 0.379 for the lexical baseline on the same split, with `parameter`, deletion volume, and add/remove ratio among the most informative features. (Result is from a single split on the medium dataset and should be treated as preliminary.)

### Code-review assistant (demo)

A small application layer that trains light intent and hole-detection models and exposes a single `review(diff)` function returning the predicted change intent plus a completeness warning when the change looks like it may be missing code.

```bash
python3 scripts/generate_holes.py --config configs/data_opentitan_medium.yaml
python3 scripts/code_review_assistant.py
```

The assistant separates complete changes (hole score ~0.2) from synthetic incomplete ones (~0.5), illustrating how the approach could assist RTL code review in practice.

## Results Reproduction

- Main results table: `outputs/metrics/main_results.csv`
- Ablation table: `outputs/metrics/ablation_results.csv`
- Full-only copies: `outputs/metrics/full_main_results.csv`, `outputs/metrics/full_ablation_results.csv`
- Smoke-only copies: `outputs/metrics/smoke_main_results.csv`, `outputs/metrics/smoke_ablation_results.csv`
- Dataset stats: `outputs/metrics/dataset_stats.json`
- Predictions: `outputs/predictions/*.jsonl`
- Figures: `outputs/figures/*.png`, `report/figures/*.png`
- Saved configs/checkpoints: `outputs/checkpoints/*`

## File Structure

- `configs/`: data/model/ablation configs (including `data_caliptra_smoke.yaml` for the generalization study and `data_opentitan_medium.yaml` for the hardware-feature model)
- `scripts/`: mining, preprocessing, training, evaluation, orchestration, and analysis scripts (including `error_analysis.py`, `generalization_study.py`, `rtl_features_model.py`, and `code_review_assistant.py`)
- `src/`: reusable data/model/training code
- `data/`: mined raw data, processed examples, and splits
- `outputs/`: checkpoints, metrics, figures, predictions, and logs
- `report/`: report draft and report assets
- `tests/`: unit tests

## Limitations

- Intent labels are weakly derived from commit messages and may be noisy. The improved keyword scheme reduces but does not eliminate this — some commit messages describe *what* changed rather than *why*, and remain unlabelable by keyword matching (motivating future LLM-based labeling).
- Synthetic holes are controlled approximations of incomplete implementations.
- The models operate on normalized textual diffs rather than HDL-specific semantic graphs.
- Full experiment runtime depends on the available CPU/GPU resources.
- The full experiment now exists on disk, but the auxiliary full ablations were run on the reference seed rather than all three seeds.
- The cross-project generalization figures were produced from smoke-scale mining limits and should be regarded as a preliminary comparison.
