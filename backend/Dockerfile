# --- Build stage: install Python deps into a venv ---
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed to build some Python packages (e.g. pymupdf, tokenizers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Runtime stage: copy only the venv + app code, no build tools ---
FROM python:3.12-slim AS runtime

# Tesseract + OpenCV runtime deps for OCR (Layer 4), included now so the
# image doesn't need rebuilding when OCR lands.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 docbot
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --chown=docbot:docbot . .

RUN mkdir -p data uploads logs && chown -R docbot:docbot data uploads logs

USER docbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
