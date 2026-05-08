#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DATA_CONFIG="${ROOT_DIR}/configs/data_opentitan_full.yaml"
SEEDS=(${SEEDS:-13 42 123})
DEVICE="${DEVICE:-auto}"
export SEEDS
export PRIMARY_ABLATION_SEEDS="${PRIMARY_ABLATION_SEEDS:-${SEEDS[*]}}"
export AUX_ABLATION_SEEDS="${AUX_ABLATION_SEEDS:-13}"
unset EPOCHS_OVERRIDE || true
export RUN_PREFIX=full
export DEVICE
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
RESOLVED_DEVICE="$("${PYTHON_BIN}" - <<'PY'
import torch
requested = "auto"
if torch.cuda.is_available():
    print("cuda")
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    print("mps")
else:
    print("cpu")
PY
)"

bash "${ROOT_DIR}/scripts/clone_repo.sh"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/extract_commits.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/build_dataset.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/generate_holes.py" --config "${DATA_CONFIG}"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/split_dataset.py" --config "${DATA_CONFIG}"

echo "Resolved device for full experiment: ${RESOLVED_DEVICE}"
if [[ "${RESOLVED_DEVICE}" == "cpu" ]]; then
  bash "${ROOT_DIR}/scripts/run_all_baselines.sh" "${DATA_CONFIG}" &
  BASELINES_PID=$!
  bash "${ROOT_DIR}/scripts/run_ablations.sh" "${DATA_CONFIG}" &
  ABLATIONS_PID=$!
  wait "${BASELINES_PID}"
  wait "${ABLATIONS_PID}"
else
  bash "${ROOT_DIR}/scripts/run_all_baselines.sh" "${DATA_CONFIG}"
  bash "${ROOT_DIR}/scripts/run_ablations.sh" "${DATA_CONFIG}"
fi

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/make_figures.py"
"${PYTHON_BIN}" "${ROOT_DIR}/scripts/make_report_assets.py"
