#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${LOCAL_VLLM_BASE_URL:-http://localhost:${LOCAL_VLLM_PORT:-9001}/v1}"
TIMEOUT_SECONDS="${LOCAL_VLLM_SMOKE_TIMEOUT_SECONDS:-600}"
PROMPT="${LOCAL_VLLM_SMOKE_PROMPT:-Reply with exactly: local model ok}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

echo "Waiting for local vLLM models endpoint: ${BASE_URL}/models"
deadline=$((SECONDS + TIMEOUT_SECONDS))
until models_json="$(curl -fsS "${BASE_URL}/models" 2>/dev/null)"; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for ${BASE_URL}/models" >&2
    echo "Check logs with: docker compose --profile local-llm logs -f llm" >&2
    exit 1
  fi
  sleep 5
done

model_id="$(
  MODELS_JSON="${models_json}" python3 - <<'PY'
import json
import os

configured = os.getenv("LOCAL_VLLM_TEST_MODEL") or os.getenv("LOCAL_VLLM_SERVED_MODEL_NAME")
if configured:
    print(configured)
    raise SystemExit

payload = json.loads(os.environ["MODELS_JSON"])
data = payload.get("data") or []
if not data:
    raise SystemExit("no models returned by /v1/models")
print(data[0]["id"])
PY
)"

echo "Testing chat completion with model: ${model_id}"
request_body="$(
  MODEL_ID="${model_id}" PROMPT="${PROMPT}" python3 - <<'PY'
import json
import os

print(json.dumps({
    "model": os.environ["MODEL_ID"],
    "messages": [
        {"role": "user", "content": os.environ["PROMPT"]},
    ],
    "max_tokens": 32,
    "temperature": 0,
}))
PY
)"

response_json="$(
  curl -fsS "${BASE_URL}/chat/completions" \
    -H "Content-Type: application/json" \
    -d "${request_body}"
)"

RESPONSE_JSON="${response_json}" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE_JSON"])
choices = payload.get("choices") or []
if not choices:
    raise SystemExit("chat completion response has no choices")

message = choices[0].get("message") or {}
content = (message.get("content") or "").strip()
if not content:
    raise SystemExit("chat completion content is empty")

usage = payload.get("usage") or {}
completion_tokens = usage.get("completion_tokens")
if completion_tokens is not None and completion_tokens <= 0:
    raise SystemExit(f"completion_tokens is not positive: {completion_tokens}")

print("OK: local vLLM generated a chat completion.")
print(f"Response: {content}")
if completion_tokens is not None:
    print(f"Completion tokens: {completion_tokens}")
PY
