FROM python:3.11-slim

# poppler-utils is required by pdf2image to convert PDF pages to images
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Disable stdout/stderr buffering so print() output appears in docker logs immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --loop asyncio avoids the uvloop/nest_asyncio incompatibility triggered
# by the semanticscholar library at import time.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
