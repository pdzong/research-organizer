FROM vllm/vllm-openai:nightly

# GLM-OCR requires the glm_ocr architecture which is only in transformers main,
# not any released version.  Install from the HEAD tarball — no git needed.
#
# `pandas` is not declared as a dependency by the nightly vLLM image but is
# imported unconditionally from `vllm/_aiter_ops.py` at startup — without it
# the entrypoint crashes with `ModuleNotFoundError: No module named 'pandas'`
# and the container restart-loops. Pin a known-good range.
RUN pip install --no-cache-dir "pandas>=2.0,<3" \
 && pip install --upgrade --no-cache-dir \
        "https://github.com/huggingface/transformers/archive/refs/heads/main.tar.gz"
