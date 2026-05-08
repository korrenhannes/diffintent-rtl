# DiffIntent-RTL Run Plan

## Objective

Build and validate an end-to-end PyTorch project for two tasks on OpenTitan SystemVerilog RTL diffs:

1. intent classification
2. implementation-hole detection

## Confirmed Course Constraints

- PyTorch is required for the deep learning implementation.
- The project must include substantial model training, not only use a frozen existing model.
- A clear baseline is required.
- Evaluation must use suitable metrics and comparisons across models.
- Results analysis must be meaningful and reproducible.
- The final report is limited to 5 pages.
- The presentation target is 15 minutes.
- Code should be organized, documented, and reproducible.

## Assumptions

- Work will be done in the current repository root instead of creating an unnecessary nested `diffintent-rtl/` directory.
- The attached execution plan and proposal define the scientific scope unless the course instructions override them.
- Smoke mode must complete on CPU even if the full experiment is too slow for this environment.
- Full experiment scripts must be complete and runnable even if only smoke mode is executed here.

## Execution Order

1. Scaffold the repository structure, configs, scripts, source modules, tests, and report folders.
2. Implement OpenTitan mining, diff parsing, weak labeling, synthetic hole generation, truncation, vocabulary building, and chronological split logic.
3. Implement reusable dataset/collation utilities for flat and hierarchical models.
4. Implement:
   - TF-IDF + logistic regression baseline
   - bag-of-tokens MLP
   - flat BiGRU
   - diff-aware hierarchical Transformer
5. Implement training, evaluation, logging, metrics, prediction export, figure generation, and CSV aggregation.
6. Implement ablation configurations and run scripts for smoke and full modes.
7. Add tests for tokenization, diff parsing, hole generation, model forward passes, and metrics stability.
8. Run `pytest`.
9. Run smoke mode end-to-end and inspect failures.
10. Generate report assets, README, project plan, and draft final report using actual saved outputs only.

## Deliverables

- Reproducible codebase and environment files
- Saved datasets, splits, metrics, figures, logs, checkpoints, and predictions
- Smoke-run results and commands
- Full-run commands and scripts
- Draft final report and project documentation
