#!/usr/bin/env python3
"""
Demonstration script for multilingual PDF outline extraction.

This script showcases the multilingual capabilities of the PDF Outline Extractor,
including Japanese, Chinese, Korean, and other language support.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import OptimizedOCRExtractor, Config, setup_logging


def demo_language_support():
    """Demonstrate language support and configuration."""
    print("PDF Outline Extractor - Multilingual Support Demo")
    print("=" * 60)
    
    # Show supported languages
    print("\n📚 Supported Languages:")
    for lang_name, tesseract_code in Config.SUPPORTED_LANGUAGES.items():
        print(f"  {lang_name:<20} -> {tesseract_code}")
    
    # Show language-specific configurations
    print("\n🔧 Language-Specific Configurations:")
    
    # English configuration
    print("\n  English Configuration:")
    config_en = Config('english')
    print(f"    Tesseract: {config_en.tesseract_lang}")
    print(f"    Patterns: {len(config_en.heading_patterns)} heading patterns")
    print(f"    Sample patterns: Chapter, Section numbers, bullet points")
    
    # Japanese configuration
    print("\n  Japanese Configuration:")
    config_jp = Config('japanese')
    print(f"    Tesseract: {config_jp.tesseract_lang}")
    print(f"    Patterns: {len(config_jp.heading_patterns)} heading patterns")
    print(f"    Sample patterns: 第X章, 目次, はじめに, まとめ")
    print(f"    Character support: Hiragana, Katakana, Kanji, numbers")
    
    # Chinese configuration
    print("\n  Chinese Configuration:")
    config_zh = Config('chinese_simplified')
    print(f"    Tesseract: {config_zh.tesseract_lang}")
    print(f"    Patterns: {len(config_zh.heading_patterns)} heading patterns")
    print(f"    Sample patterns: 第X章, 目录, 概述, 结论")
    
    # Korean configuration
    print("\n  Korean Configuration:")
    config_ko = Config('korean')
    print(f"    Tesseract: {config_ko.tesseract_lang}")
    print(f"    Patterns: {len(config_ko.heading_patterns)} heading patterns")
    print(f"    Sample patterns: 제X장, 목차, 서론, 결론")


def demo_language_detection():
    """Demonstrate automatic language detection."""
    print("\n🔍 Language Detection Demo:")
    
    # Test samples
    samples = [
        ("English sample", "Chapter 1: Introduction\nThis document contains..."),
        ("Japanese sample", "第１章：はじめに\nこの文書は日本語で書かれています。"),
        ("Chinese sample", "第一章：概述\n这是一个中文文档的例子。"),
        ("Korean sample", "제1장: 개요\n이것은 한국어 문서의 예입니다."),
        ("Mixed sample", "Chapter 1: 日本語 and English mixed content")
    ]
    
    for sample_name, text in samples:
        detected = Config.detect_language(text)
        print(f"  {sample_name:<15} -> {detected}")


def demo_extractor_usage():
    """Demonstrate how to use the extractor with different languages."""
    print("\n⚙️  Extractor Usage Examples:")
    
    print("\n  # English (default)")
    print("  extractor = OptimizedOCRExtractor('english')")
    
    print("\n  # Japanese with auto-detection")
    print("  extractor = OptimizedOCRExtractor('japanese', auto_detect_language=True)")
    
    print("\n  # Chinese Simplified")
    print("  extractor = OptimizedOCRExtractor('chinese_simplified')")
    
    print("\n  # Auto-detect language for each PDF")
    print("  extractor = OptimizedOCRExtractor('english', auto_detect_language=True)")


def demo_command_line_usage():
    """Show command line usage examples."""
    print("\n💻 Command Line Usage Examples:")
    
    examples = [
        ("Basic English processing", "python main_modular.py -i pdfs/ -o outputs/"),
        ("Japanese PDFs", "python main_modular.py -i japanese_pdfs/ -o outputs/ --language japanese"),
        ("Auto-detect per file", "python main_modular.py -i mixed_pdfs/ -o outputs/ --auto-detect"),
        ("Single Japanese file", "python main_modular.py -s document.pdf -o outputs/ --language japanese"),
        ("Verbose Chinese processing", "python main_modular.py -i chinese_docs/ -o outputs/ -l chinese_simplified -v"),
        ("List all languages", "python main_modular.py --list-languages"),
        ("High performance batch", "python main_modular.py -i large_batch/ -o outputs/ -w 8 --auto-detect")
    ]
    
    for description, command in examples:
        print(f"\n  # {description}")
        print(f"  {command}")


def demo_json_output():
    """Show sample JSON output structure."""
    print("\n📄 Sample JSON Output Structure:")
    
    sample_output = '''
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
      "level": "H2",
      "text": "1.2 機械学習の種類",
      "page": 3
    },
    {
      "level": "H3",
      "text": "1.2.1 教師あり学習",
      "page": 4
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
}'''
    
    print(sample_output)


def demo_docker_usage():
    """Show Docker usage for multilingual support."""
    print("\n🐳 Docker Usage for Multilingual Support:")
    
    print("\n  # Build image with multilingual support")
    print("  ./build-docker.sh")
    
    print("\n  # Process Japanese PDFs")
    print("  docker run --rm \\")
    print("    -v $(pwd)/japanese_pdfs:/app/input \\")
    print("    -v $(pwd)/outputs:/app/output \\")
    print("    pdf-outline-extractor python main.py -i /app/input -o /app/output --language japanese")
    
    print("\n  # Auto-detect language")
    print("  docker run --rm \\")
    print("    -v $(pwd)/mixed_pdfs:/app/input \\")
    print("    -v $(pwd)/outputs:/app/output \\")
    print("    pdf-outline-extractor python main.py -i /app/input -o /app/output --auto-detect")


def main():
    """Run the complete demonstration."""
    setup_logging('INFO')
    
    try:
        demo_language_support()
        demo_language_detection()
        demo_extractor_usage()
        demo_command_line_usage()
        demo_json_output()
        demo_docker_usage()
        
        print("\n" + "=" * 60)
        print("✅ Demo complete! The extractor is ready for multilingual PDF processing.")
        print("\nTo get started:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Install Tesseract language packs (see Dockerfile for list)")
        print("3. Run: python main_modular.py --help")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
