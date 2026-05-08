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
PRIMARY_ABLATION_SEEDS=(${PRIMARY_ABLATION_SEEDS:-${SEEDS[*]}})
DEFAULT_AUX_SEED="${SEEDS[0]}"
AUX_ABLATION_SEEDS=(${AUX_ABLATION_SEEDS:-${DEFAULT_AUX_SEED}})

should_skip_run() {
  local run_name="$1"
  local metrics_path="${ROOT_DIR}/outputs/metrics/${run_name}_test_metrics.json"
  if [[ "${FORCE_RERUN}" != "1" && -f "${metrics_path}" ]]; then
    echo "Skipping completed run ${run_name}"
    return 0
  fi
  return 1
}

for seed in "${PRIMARY_ABLATION_SEEDS[@]}"; do
  name_prefix=""
  if [[ -n "${RUN_PREFIX}" ]]; then
    name_prefix="${RUN_PREFIX}_"
  fi

  run_name="${name_prefix}hierarchical_no_line_type_seed${seed}"
  no_line_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/ablation_no_line_type.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    no_line_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${no_line_cmd[@]}"
  fi

done

for seed in "${AUX_ABLATION_SEEDS[@]}"; do
  name_prefix=""
  if [[ -n "${RUN_PREFIX}" ]]; then
    name_prefix="${RUN_PREFIX}_"
  fi

  run_name="${name_prefix}hierarchical_no_context_seed${seed}"
  no_context_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/ablation_no_context.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    no_context_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${no_context_cmd[@]}"
  fi

  run_name="${name_prefix}tfidf_message_only_seed${seed}"
  if ! should_skip_run "${run_name}"; then
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train_tfidf.py" \
    --config "${ROOT_DIR}/configs/ablation_message_only.yaml" \
    --data-config "${DATA_CONFIG}" \
    --run-name "${run_name}" \
    --seed "${seed}"
  fi

  run_name="${name_prefix}hierarchical_no_multitask_intent_seed${seed}"
  no_multitask_intent_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/ablation_no_multitask.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
    --task-mode-override "intent_only"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    no_multitask_intent_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${no_multitask_intent_cmd[@]}"
  fi

  run_name="${name_prefix}hierarchical_no_multitask_hole_seed${seed}"
  no_multitask_hole_cmd=(
    "${PYTHON_BIN}" "${ROOT_DIR}/scripts/train.py"
    --config "${ROOT_DIR}/configs/ablation_no_multitask.yaml"
    --data-config "${DATA_CONFIG}"
    --run-name "${run_name}"
    --seed "${seed}"
    --device "${DEVICE}"
    --task-mode-override "hole_only"
  )
  if [[ -n "${EPOCHS_OVERRIDE:-}" ]]; then
    no_multitask_hole_cmd+=(--epochs-override "${EPOCHS_OVERRIDE}")
  fi
  if ! should_skip_run "${run_name}"; then
    "${no_multitask_hole_cmd[@]}"
  fi
done
