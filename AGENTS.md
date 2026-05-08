# AGENTS

## Repository Intent

This repository implements the DiffIntent-RTL course project end-to-end:

- OpenTitan RTL diff mining
- weak intent labeling
- synthetic implementation-hole generation
- TF-IDF and PyTorch training/evaluation
- smoke/full experiment orchestration

## Working Conventions

- Run everything from the repository root.
- Use configs under `configs/` rather than hard-coded paths.
- Preserve train/validation/test chronology and pair integrity for synthetic holes.
- Build vocabulary from the train split only.
- Save all metrics, predictions, figures, and configs to `outputs/`.

## Primary Commands

- `bash scripts/run_smoke.sh`
- `bash scripts/run_full_experiment.sh`
- `python3 -m pytest tests`

