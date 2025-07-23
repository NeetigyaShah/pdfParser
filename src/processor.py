"""
Batch processing module for handling multiple PDF files.
Provides parallel processing and progress tracking.
"""

import os
import json
import time
import concurrent.futures
import logging
from pathlib import Path
from typing import Dict, Any, List

from .extractor import OptimizedOCRExtractor
from .utils import ProgressTracker, get_file_info, format_processing_time, validate_pdf_file


logger = logging.getLogger(__name__)


class BatchProcessor:
    """Optimized batch processor with multilingual support."""
    
    def __init__(self, language: str = 'english', max_workers: int = None, auto_detect_language: bool = True):
        """
        Initialize batch processor.
        
        Args:
            language: Default language for processing
            max_workers: Maximum number of parallel workers
            auto_detect_language: Whether to auto-detect language per PDF
        """
        self.language = language
        self.max_workers = max_workers or min(8, (os.cpu_count() or 4))
        self.auto_detect_language = auto_detect_language
        
        logger.info(f"Initialized batch processor:")
        logger.info(f"  Language: {language}")
        logger.info(f"  Workers: {self.max_workers}")
        logger.info(f"  Auto-detect language: {auto_detect_language}")
    
    def process_single_pdf(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single PDF file with comprehensive error handling.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output JSON files
        
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        
        try:
            # Validate PDF file
            if not validate_pdf_file(pdf_path):
                raise ValueError(f"Invalid or corrupted PDF file: {pdf_path.name}")
            
            # Get file info for logging
            file_info = get_file_info(pdf_path)
            logger.debug(f"Processing {pdf_path.name} ({file_info['size_mb']} MB)")
            
            # Create extractor with language settings
            extractor = OptimizedOCRExtractor(
                language=self.language,
                auto_detect_language=self.auto_detect_language
            )
            
            # Extract outline
            result = extractor.extract_outline(str(pdf_path))
            
            # Create schema-compliant output
            output_data = {
                "title": result["title"],
                "outline": result["outline"],
                "metadata": {
                    "source_file": pdf_path.name,
                    "processing_time": result["_stats"]["processing_time"],
                    "language": result["_stats"]["language"],
                    "detected_language": result["_stats"].get("detected_language"),
                    "total_lines_processed": result["_stats"]["total_lines"],
                    "headings_found": result["_stats"]["headings_found"],
                    "file_size_mb": file_info["size_mb"]
                }
            }
            
            # Save to JSON file
            output_file = output_dir / f"{pdf_path.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "pdf_path": str(pdf_path),
                "output_file": str(output_file),
                "processing_time": processing_time,
                "headings_found": len(result["outline"]),
                "title": result["title"],
                "language": result["_stats"]["language"],
                "detected_language": result["_stats"].get("detected_language"),
                "file_size_mb": file_info["size_mb"]
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing {pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "pdf_path": str(pdf_path),
                "error": str(e),
                "processing_time": processing_time,
                "headings_found": 0,
                "file_size_mb": get_file_info(pdf_path).get("size_mb", 0)
            }
    
    def process_batch(self, input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Process multiple PDFs in parallel with comprehensive tracking.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory for output JSON files
        
        Returns:
            Batch processing results
        """
        # Find all PDF files
        pdf_files = [f for f in input_dir.glob("*.pdf") if validate_pdf_file(f)]
        
        if not pdf_files:
            error_msg = f"No valid PDF files found in {input_dir}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "total_files": 0,
                "successful": [],
                "failed": []
            }
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate total file size for estimation
        total_size_mb = sum(get_file_info(f)["size_mb"] for f in pdf_files)
        
        logger.info(f"Starting batch processing:")
        logger.info(f"  Files: {len(pdf_files)}")
        logger.info(f"  Total size: {total_size_mb:.1f} MB")
        logger.info(f"  Output directory: {output_dir}")
        
        start_time = time.time()
        progress = ProgressTracker(len(pdf_files), "PDF Processing")
        
        results = {
            "total_files": len(pdf_files),
            "total_size_mb": total_size_mb,
            "successful": [],
            "failed": [],
            "total_time": 0,
            "languages_detected": set()
        }
        
        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="PDF-Worker"
        ) as executor:
            
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_file, output_dir): pdf_file
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf_file = future_to_pdf[future]
                result = future.result()
                
                # Update progress
                progress.update(1, pdf_file.name)
                
                if result["success"]:
                    results["successful"].append(result)
                    
                    # Track languages
                    if result.get("language"):
                        results["languages_detected"].add(result["language"])
                    if result.get("detected_language"):
                        results["languages_detected"].add(result["detected_language"])
                    
                    logger.info(
                        f"✓ {pdf_file.name}: {result['headings_found']} headings "
                        f"({result['language']}) in {format_processing_time(result['processing_time'])}"
                    )
                else:
                    results["failed"].append(result)
                    logger.error(f"✗ {pdf_file.name}: {result['error']}")
        
        results["total_time"] = time.time() - start_time
        results["languages_detected"] = list(results["languages_detected"])
        
        # Finalize progress and print summary
        progress.finish("All files processed")
        self._print_detailed_summary(results)
        
        return results
    
    def _print_detailed_summary(self, results: Dict[str, Any]) -> None:
        """
        Print comprehensive processing summary.
        
        Args:
            results: Batch processing results
        """
        logger.info("\n" + "="*70)
        logger.info("BATCH PROCESSING SUMMARY")
        logger.info("="*70)
        
        # Basic statistics
        logger.info(f"Total files processed: {results['total_files']}")
        logger.info(f"Successful: {len(results['successful'])}")
        logger.info(f"Failed: {len(results['failed'])}")
        
        if results['total_files'] > 0:
            success_rate = len(results['successful']) / results['total_files'] * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        # Timing statistics
        logger.info(f"Total processing time: {format_processing_time(results['total_time'])}")
        if results['total_files'] > 0:
            avg_time = results['total_time'] / results['total_files']
            logger.info(f"Average time per file: {format_processing_time(avg_time)}")
        
        # Size and throughput
        logger.info(f"Total data processed: {results['total_size_mb']:.1f} MB")
        if results['total_time'] > 0:
            throughput = results['total_size_mb'] / results['total_time']
            logger.info(f"Processing throughput: {throughput:.2f} MB/s")
        
        # Content statistics
        if results['successful']:
            total_headings = sum(r['headings_found'] for r in results['successful'])
            avg_headings = total_headings / len(results['successful'])
            logger.info(f"Total headings extracted: {total_headings}")
            logger.info(f"Average headings per file: {avg_headings:.1f}")
        
        # Language detection results
        if results['languages_detected']:
            logger.info(f"Languages detected: {', '.join(results['languages_detected'])}")
        
        # Error summary
        if results['failed']:
            logger.info("\nERROR SUMMARY:")
            error_types = {}
            for failed in results['failed']:
                error = failed['error']
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                logger.info(f"  {error}: {count} file(s)")
        
        logger.info("="*70)
