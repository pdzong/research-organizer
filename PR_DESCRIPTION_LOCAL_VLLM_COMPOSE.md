# Add optional local vLLM Docker Compose setup

## Summary

- Add an optional `local-llm` Docker Compose profile for serving Qwen3.6 through vLLM on port `9001`.
- Add local vLLM environment knobs to `.env.example`.
- Add `scripts/start-local-vllm.sh` with preflight checks and clear setup guidance when `spark-vllm-docker` is missing.
- Add `scripts/smoke-local-vllm.sh` to verify `/v1/models` and `/v1/chat/completions`.
- Document the local vLLM smoke test in `TESTING.md`.

## Notes

This PR only adds the Docker Compose/runtime setup for the local model. It does not wire the local vLLM endpoint into the backend LLM provider registry yet.

The Compose service expects a local `spark-vllm-docker/` checkout because it uses that repo as the Docker build context and mounts the Qwen 3.6 chat template. The new start script now prints explicit clone instructions when that checkout is missing.

## Validation

- `bash scripts/start-local-vllm.sh --check`
- `docker compose --profile local-llm config --quiet`
- `bash -n scripts/start-local-vllm.sh`
- `bash -n scripts/smoke-local-vllm.sh`
- `bash scripts/smoke-local-vllm.sh`

The smoke test successfully reached the running local vLLM endpoint on `localhost:9001`, listed the served model, and received a non-empty chat completion.
