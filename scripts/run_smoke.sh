#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DATA_CONFIG="${ROOT_DIR}/configs/data_opentitan_smoke.yaml"
SEEDS=(${SEEDS:-13 42 123})
DEVICE="${DEVICE:-auto}"
export SEEDS
export EPOCHS_OVERRIDE=2
export RUN_PREFIX=smoke
export DEVICE
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"

bash "${ROOT_DIR}/scripts/clone_repo.sh"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/extract_commits.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/build_dataset.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/generate_holes.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/split_dataset.py" --config "${DATA_CONFIG}"

bash "${ROOT_DIR}/scripts/run_all_baselines.sh" "${DATA_CONFIG}"
bash "${ROOT_DIR}/scripts/run_ablations.sh" "${DATA_CONFIG}"

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/make_figures.py"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/make_report_assets.py"
