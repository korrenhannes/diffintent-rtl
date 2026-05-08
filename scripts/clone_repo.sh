#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${ROOT_DIR}/external/opentitan"
REPO_URL="https://github.com/lowRISC/opentitan.git"

mkdir -p "${ROOT_DIR}/external"

if [[ -d "${REPO_DIR}/.git" ]]; then
  echo "Reusing existing git repository at ${REPO_DIR}"
  exit 0
fi

if [[ -d "${REPO_DIR}" ]]; then
  echo "Path exists but is not a git repository: ${REPO_DIR}" >&2
  exit 1
fi

git clone "${REPO_URL}" "${REPO_DIR}"

