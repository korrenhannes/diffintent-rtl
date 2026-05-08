# DiffIntent-RTL

DiffIntent-RTL is a PyTorch-based course project for understanding SystemVerilog RTL code changes from OpenTitan history. The repository builds a dataset from real commits, weakly labels change intent, generates synthetic implementation holes, and compares lexical baselines against neural diff models.

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

## Data Construction

The pipeline mines modified `hw/**/rtl/*.sv` files from OpenTitan while excluding DV, test, vendor, third-party, generated, build, and output paths.

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

## Results Reproduction

- Main results table: `outputs/metrics/main_results.csv`
- Ablation table: `outputs/metrics/ablation_results.csv`
- Full-only copies: `outputs/metrics/full_main_results.csv`, `outputs/metrics/full_ablation_results.csv`
- Smoke-only copies: `outputs/metrics/smoke_main_results.csv`, `outputs/metrics/smoke_ablation_results.csv`
- Dataset stats: `outputs/metrics/dataset_stats.json`
- Predictions: `outputs/predictions/*.jsonl`
- Figures: `outputs/figures/*.png`
- Saved configs/checkpoints: `outputs/checkpoints/*`

## File Structure

- `configs/`: data/model/ablation configs
- `scripts/`: mining, preprocessing, training, evaluation, and orchestration scripts
- `src/`: reusable data/model/training code
- `data/`: mined raw data, processed examples, and splits
- `outputs/`: checkpoints, metrics, figures, predictions, and logs
- `report/`: report draft and report assets
- `tests/`: unit tests

## Limitations

- Intent labels are weakly derived from commit messages and may be noisy.
- Synthetic holes are controlled approximations of incomplete implementations.
- The models operate on normalized textual diffs rather than HDL-specific semantic graphs.
- Full experiment runtime depends on the available CPU/GPU resources.
- The full experiment now exists on disk, but the auxiliary full ablations were run on the reference seed rather than all three seeds.
