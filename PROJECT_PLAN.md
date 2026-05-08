# DiffIntent-RTL Project Plan

## Goal

Train and evaluate models that infer the intent of SystemVerilog RTL diffs and detect suspicious incomplete changes mined from OpenTitan history.

## Tasks

1. Change intent classification:
   - `bug_fix`
   - `feature_or_behavior_change`
   - `refactor_cleanup`
   - `configuration_timing`
2. Implementation-hole detection:
   - `complete`
   - `synthetic_hole`

## Data Construction

- Repository: `lowRISC/opentitan`
- Primary scope: `hw/**/rtl/*.sv`
- Exclusions: DV, tests, vendor, third-party, generated, build, and output paths
- Weak labels from commit-message keyword patterns
- Synthetic holes generated from accepted real diffs through controlled line/hunk/operator mutations
- Chronological split with pair-preserving grouping

## Models

- TF-IDF + logistic regression
- Bag-of-tokens MLP
- Flat BiGRU with attention pooling
- Diff-aware hierarchical Transformer with line-type embeddings

## Required Comparisons

- Baselines vs. hierarchical Transformer
- `no_line_type_embeddings`
- `no_multitask`
- `no_context_lines`
- `message_only`
- default diff-only setting

## Evaluation

- Intent: accuracy, macro-F1, weighted-F1, per-class precision/recall/F1, confusion matrix
- Hole detection: accuracy, precision, recall, F1, AUROC, PR-AUC, confusion matrix

## Reproducibility

- Fixed seeds: `13`, `42`, `123`
- YAML configs for data and models
- Saved metrics, predictions, figures, and run configs under `outputs/`
- Draft report assets under `report/`

