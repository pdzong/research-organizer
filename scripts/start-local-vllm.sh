#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPARK_VLLM_DIR="${ROOT_DIR}/spark-vllm-docker"
CHECK_ONLY=false

if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
  shift
fi

print_missing_spark_vllm() {
  cat >&2 <<EOF
Local vLLM setup is missing the spark-vllm-docker checkout.

Expected directory:
  ${SPARK_VLLM_DIR}

Clone it before starting the local-llm Docker Compose profile:
  cd ${ROOT_DIR}
  git clone https://github.com/eugr/spark-vllm-docker.git

Then start the local model service:
  bash scripts/start-local-vllm.sh
EOF
}

print_missing_template() {
  cat >&2 <<EOF
Local vLLM setup found spark-vllm-docker, but it is missing the Qwen 3.6 chat template.

Expected file:
  ${SPARK_VLLM_DIR}/mods/fix-qwen3.6-chat-template/chat_template.jinja

Refresh the checkout and try again:
  cd ${SPARK_VLLM_DIR}
  git pull
EOF
}

if [[ ! -d "${SPARK_VLLM_DIR}" || ! -f "${SPARK_VLLM_DIR}/Dockerfile" ]]; then
  print_missing_spark_vllm
  exit 1
fi

if [[ ! -f "${SPARK_VLLM_DIR}/mods/fix-qwen3.6-chat-template/chat_template.jinja" ]]; then
  print_missing_template
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to start the local vLLM service, but 'docker' is not on PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  cat >&2 <<EOF
Docker Compose is required to start the local vLLM service.

Make sure Docker is running and that your user can access the Docker daemon.
If Docker requires sudo on this machine, run:
  sudo bash scripts/start-local-vllm.sh
EOF
  exit 1
fi

if [[ "${CHECK_ONLY}" == "true" ]]; then
  echo "OK: local vLLM prerequisites are present."
  exit 0
fi

cd "${ROOT_DIR}"
exec docker compose --profile local-llm up --build llm "$@"
