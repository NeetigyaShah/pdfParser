# Use official Python 3.10 slim image for AMD64
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install Tesseract OCR + OpenCV dependencies + libcrypt for PyMuPDF compatibility
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-por \
        tesseract-ocr-fra \
        tesseract-ocr-deu \
        tesseract-ocr-ita \
        tesseract-ocr-jpn \
        tesseract-ocr-chi-sim \
        tesseract-ocr-kor \
        tesseract-ocr-rus \
        tesseract-ocr-ell \
        tesseract-ocr-ara \
        tesseract-ocr-hin \
        libcrypt1 \
        libcrypt-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcrypt.so.1 /usr/lib/x86_64-linux-gnu/libcrypt.so.2 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main_modular.py .
COPY src/ src/

# Prepare input/output dirs
RUN mkdir -p /app/input /app/output

# Performance env vars
ENV PYTHONUNBUFFERED=1 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Default command: auto-process all PDFs → JSONs
CMD ["python", "main_modular.py", \
     "-i", "/app/input", \
     "-o", "/app/output", \
     "--auto-detect", \
     "-w", "4"]