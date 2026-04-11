FROM vllm/vllm-openai:nightly

# GLM-OCR requires the glm_ocr architecture which is only in transformers main,
# not any released version.  Install from the HEAD tarball — no git needed.
RUN pip install --upgrade "https://github.com/huggingface/transformers/archive/refs/heads/main.tar.gz"
