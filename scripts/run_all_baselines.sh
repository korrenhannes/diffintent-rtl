#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_CONFIG="${1:-${ROOT_DIR}/configs/data_opentitan_smoke.yaml}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SEEDS=(${SEEDS:-13 42 123})
RUN_PREFIX="${RUN_PREFIX:-}"
DEVICE="${DEVICE:-auto}"
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
FORCE_RERUN="${FORCE_RERUN:-0}"

should_skip_run() {
  local run_name="$1"
  local metrics_path="${ROOT_DIR}/outputs/metrics/${run_name}_test_metrics.json"
  if [[ "${FORCE_RERUN}" != "1" && -f "${metrics_path}" ]]; then
    echo "Skipping completed run ${run_name}"
    return 0
  fi
  return 1
}

for seed in "${SEEDS[@]}"; do
  name_prefix=""
  if [[ -n "${RUN_PREFIX}" ]]; then
    name_prefix="${RUN_PREFIX}_"
  fi

  run_name="${name_prefix}tfidf_lr_seed${seed}"
  if ! should_skip_run "${run_name}"; then
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train_tfidf.py" \
    --config "${ROOT_DIR}/configs/tfidf_lr.yaml" \
    --data-config "${DATA_CONFIG}" \
    --run-name "${run_name}" \
    --seed "${seed}"
  fi

  run_name="${name_prefix}mlp_seed${seed}"
  mlp_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/mlp.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    mlp_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${mlp_cmd[@]}"
  fi

  run_name="${name_prefix}bigru_seed${seed}"
  bigru_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/bigru.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    bigru_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${bigru_cmd[@]}"
  fi

  run_name="${name_prefix}hierarchical_transformer_seed${seed}"
  htrans_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/hierarchical_transformer.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    htrans_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${htrans_cmd[@]}"
  fi
done
