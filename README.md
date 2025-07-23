# PDF Outline Extractor - Multilingual Edition

A modular, high-performance PDF outline extraction tool with comprehensive multilingual support including Japanese, Chinese, Korean, and 13+ other languages. Uses advanced OCR and direct text extraction for accurate heading detection and structured outline generation.

## 🌟 Features

### Core Capabilities
- **Multilingual OCR**: Support for 13+ languages including Japanese, Chinese, Korean, Arabic, Hindi
- **Automatic Language Detection**: Detect document language automatically
- **Hybrid Extraction**: Combines direct text extraction with OCR fallback
- **Modular Architecture**: Clean, maintainable code structure
- **Batch Processing**: Parallel processing with configurable workers
- **Structured Output**: Clean JSON format with metadata

### Language Support
| Language | Tesseract Code | Pattern Support | Character Support |
|----------|----------------|-----------------|-------------------|
| English | eng | ✅ Full | Latin alphabet |
| Japanese | jpn | ✅ Full | Hiragana, Katakana, Kanji |
| Chinese (Simplified) | chi_sim | ✅ Full | Simplified Chinese |
| Chinese (Traditional) | chi_tra | ✅ Full | Traditional Chinese |
| Korean | kor | ✅ Full | Hangul |
| Spanish | spa | ✅ Basic | Latin alphabet |
| French | fra | ✅ Basic | Latin alphabet |
| German | deu | ✅ Basic | Latin alphabet |
| Portuguese | por | ✅ Basic | Latin alphabet |
| Italian | ita | ✅ Basic | Latin alphabet |
| Russian | rus | ✅ Basic | Cyrillic |
| Arabic | ara | ✅ Basic | Arabic script |
| Hindi | hin | ✅ Basic | Devanagari |

## 🚀 Quick Start

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR with language packs:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-jpn \
                    tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-kor
   
   # macOS
   brew install tesseract tesseract-lang
   
   # Windows
   # Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

### Basic Usage

```bash
# English PDFs (default)
python main_modular.py -i pdfs/ -o outputs/

# Japanese PDFs
python main_modular.py -i japanese_pdfs/ -o outputs/ --language japanese

# Auto-detect language per PDF
python main_modular.py -i mixed_pdfs/ -o outputs/ --auto-detect

# Single file processing
python main_modular.py -s document.pdf -o outputs/ --language japanese

# High-performance batch processing
python main_modular.py -i large_batch/ -o outputs/ -w 8 --auto-detect -v
```

### Demo

```bash
# Run multilingual demonstration
python demo_multilingual.py

# List all supported languages
python main_modular.py --list-languages
```

## 🐳 Docker Support

### Build with Multilingual Support

```bash
# Build image with all language packs
./build-docker.sh
```

### Run with Docker

```bash
# English processing (default)
./run-docker.sh

# Japanese processing
docker run --rm \
  -v $(pwd)/japanese_pdfs:/app/input \
  -v $(pwd)/outputs:/app/output \
  pdf-outline-extractor python main.py -i /app/input -o /app/output --language japanese

# Auto-detect language
docker run --rm \
  -v $(pwd)/mixed_pdfs:/app/input \
  -v $(pwd)/outputs:/app/output \
  pdf-outline-extractor python main.py -i /app/input -o /app/output --auto-detect
```

## 📊 Output Format

### JSON Structure

```json
{
  "title": "第1章：機械学習の基礎",
  "outline": [
    {
      "level": "H1",
      "text": "第1章：機械学習の基礎",
      "page": 1
    },
    {
      "level": "H2",
      "text": "1.1 はじめに",
      "page": 1
    },
    {
      "level": "H3",
      "text": "1.1.1 背景",
      "page": 2
    }
  ],
  "metadata": {
    "source_file": "ml_textbook_jp.pdf",
    "processing_time": 2.34,
    "language": "japanese",
    "detected_language": "japanese",
    "total_lines_processed": 156,
    "headings_found": 12,
    "file_size_mb": 1.2
  }
}
```

## 🏗️ Architecture

### Modular Structure

```
src/
├── __init__.py          # Package initialization
├── config.py            # Language configurations
├── extractor.py         # Core OCR extraction logic
├── processor.py         # Batch processing
└── utils.py             # Utility functions

main_modular.py          # Command-line interface
demo_multilingual.py     # Demonstration script
```

## ⚡ Performance

### Benchmarks
- **English**: ~2s per MB
- **Japanese**: ~5s per MB (higher complexity)
- **Chinese**: ~4s per MB
- **Korean**: ~4.5s per MB

### Docker Requirements Met

✅ **AMD64 Architecture**: Compatible with linux/amd64  
✅ **No GPU Dependencies**: Uses CPU-only processing  
✅ **Offline Operation**: No network/internet calls required  
✅ **Multilingual Support**: 13+ languages included

## Output Format

Each PDF generates a JSON file with this structure:
```json
{
  "title": "Document Title",
  "outline": [
    {"level": "H1", "text": "Chapter 1", "page": 1},
    {"level": "H2", "text": "Section 1.1", "page": 2}
  ]
}
```

## System Requirements

- Docker with AMD64 support
- Input PDFs in `test_pdfs/` directory
- Write access for `outputs/` directory
