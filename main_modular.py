#!/usr/bin/env python3
"""
PDF Outline Extractor - Modular multilingual PDF outline extraction tool.

This is the main entry point for the application. It provides a command-line
interface for extracting structured outlines from PDF files with support for
multiple languages including Japanese, Chinese, Korean, and others.

Features:
- Multilingual OCR support (13+ languages)
- Automatic language detection
- Batch processing with parallel execution
- Both direct text extraction and OCR fallback
- Structured JSON output
- Comprehensive error handling and logging

Usage:
    python main.py -i input_dir -o output_dir [options]

Examples:
    # Basic usage (English)
    python main.py -i pdfs/ -o outputs/
    
    # Japanese PDFs with auto-detection
    python main.py -i japanese_pdfs/ -o outputs/ --language japanese
    
    # Auto-detect language per PDF
    python main.py -i mixed_pdfs/ -o outputs/ --auto-detect
    
    # High verbosity with 8 workers
    python main.py -i pdfs/ -o outputs/ -w 8 -v
"""

import sys
import argparse
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import OptimizedOCRExtractor, BatchProcessor, Config, setup_logging


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Multilingual PDF outline extraction with OCR support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported Languages:
  english, japanese, chinese_simplified, chinese_traditional, korean,
  spanish, french, german, portuguese, italian, russian, arabic, hindi

Examples:
  %(prog)s -i pdfs/ -o outputs/
  %(prog)s -i japanese_docs/ -o results/ --language japanese
  %(prog)s -i mixed_docs/ -o results/ --auto-detect -w 4 -v
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--input", "-i", 
        required=False,  # Made optional to allow --list-languages
        type=Path,
        help="Input directory containing PDF files"
    )
    
    parser.add_argument(
        "--output", "-o", 
        required=False,  # Made optional to allow --list-languages
        type=Path,
        help="Output directory for JSON files"
    )
    
    # Language options
    parser.add_argument(
        "--language", "-l",
        default="english",
        choices=list(Config.SUPPORTED_LANGUAGES.keys()),
        help="Target language for OCR processing (default: english)"
    )
    
    parser.add_argument(
        "--auto-detect", "-a",
        action="store_true",
        help="Auto-detect language for each PDF (overrides --language per file)"
    )
    
    # Processing options
    parser.add_argument(
        "--workers", "-w",
        type=int,
        help="Number of parallel workers (default: auto-detect based on CPU cores)"
    )
    
    parser.add_argument(
        "--single", "-s",
        metavar="PDF_FILE",
        type=Path,
        help="Process a single PDF file instead of batch processing"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimize output (ERROR level only)"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Save logs to specified file"
    )
    
    # Advanced options
    parser.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable automatic language detection (use specified language only)"
    )
    
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported languages and exit"
    )
    
    return parser


def setup_application_logging(args) -> None:
    """Set up logging based on command line arguments."""
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    
    log_file = str(args.log_file) if args.log_file else None
    setup_logging(log_level, log_file)


def list_supported_languages() -> None:
    """List all supported languages and their Tesseract codes."""
    print("Supported Languages:")
    print("=" * 50)
    
    for lang_name, tesseract_code in Config.SUPPORTED_LANGUAGES.items():
        print(f"  {lang_name:<20} -> {tesseract_code}")
    
    print("\nUsage:")
    print("  --language japanese")
    print("  --language chinese_simplified")
    print("  --auto-detect  (detect language automatically)")


def validate_arguments(args) -> bool:
    """Validate command line arguments."""
    # Check if listing languages
    if args.list_languages:
        list_supported_languages()
        return False
    
    # For single file processing, only output is required
    if args.single:
        if not args.output:
            print("Error: --output is required", file=sys.stderr)
            return False
        if not args.single.exists():
            print(f"Error: Single PDF file not found: {args.single}", file=sys.stderr)
            return False
        if args.single.suffix.lower() != '.pdf':
            print(f"Error: File is not a PDF: {args.single}", file=sys.stderr)
            return False
    else:
        # For batch processing, both input and output are required
        if not args.input:
            print("Error: --input is required for batch processing", file=sys.stderr)
            return False
        if not args.output:
            print("Error: --output is required", file=sys.stderr)
            return False
        if not args.input.exists():
            print(f"Error: Input directory not found: {args.input}", file=sys.stderr)
            return False
        if not args.input.is_dir():
            print(f"Error: Input path is not a directory: {args.input}", file=sys.stderr)
            return False
    
    # Validate conflicting options
    if args.quiet and args.verbose:
        print("Error: Cannot use both --quiet and --verbose", file=sys.stderr)
        return False
    
    if args.auto_detect and args.no_auto_detect:
        print("Error: Cannot use both --auto-detect and --no-auto-detect", file=sys.stderr)
        return False
    
    return True


def process_single_file(args) -> int:
    """Process a single PDF file."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing single file: {args.single.name}")
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Create processor
    processor = BatchProcessor(
        language=args.language,
        max_workers=1,  # Single file doesn't need multiple workers
        auto_detect_language=args.auto_detect and not args.no_auto_detect
    )
    
    # Process the file
    start_time = time.time()
    result = processor.process_single_pdf(args.single, args.output)
    total_time = time.time() - start_time
    
    # Print results
    if result["success"]:
        logger.info(f"✅ Success!")
        logger.info(f"   Title: {result['title']}")
        logger.info(f"   Headings found: {result['headings_found']}")
        logger.info(f"   Language: {result['language']}")
        if result.get('detected_language'):
            logger.info(f"   Detected language: {result['detected_language']}")
        logger.info(f"   Processing time: {total_time:.2f}s")
        logger.info(f"   Output: {result['output_file']}")
        return 0
    else:
        logger.error(f"❌ Failed: {result['error']}")
        return 1


def process_batch(args) -> int:
    """Process multiple PDF files in batch."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting batch processing")
    logger.info(f"Input directory: {args.input}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Language: {args.language}")
    
    # Create processor
    processor = BatchProcessor(
        language=args.language,
        max_workers=args.workers,
        auto_detect_language=args.auto_detect and not args.no_auto_detect
    )
    
    # Process all files
    start_time = time.time()
    results = processor.process_batch(args.input, args.output)
    total_time = time.time() - start_time
    
    # Print final summary
    if results.get("success", True):  # Batch can be partially successful
        logger.info(f"\n🎉 Batch processing complete!")
        logger.info(f"   Total time: {total_time:.2f}s")
        
        if len(results['failed']) == 0:
            logger.info("   All files processed successfully!")
            return 0
        else:
            logger.warning(f"   {len(results['failed'])} file(s) failed")
            return 1
    else:
        logger.error(f"❌ Batch processing failed: {results.get('error', 'Unknown error')}")
        return 1


def main() -> int:
    """Main application entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not validate_arguments(args):
        return 1
    
    # Set up logging
    setup_application_logging(args)
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("PDF Outline Extractor - Multilingual Edition")
    logger.info(f"Language: {args.language}")
    
    try:
        # Process based on mode
        if args.single:
            return process_single_file(args)
        else:
            return process_batch(args)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Processing interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main())
