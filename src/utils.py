"""
Utility functions for PDF Outline Extractor.
Provides logging setup and helper functions.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)


def validate_pdf_file(file_path: Path) -> bool:
    """
    Validate if a file is a valid PDF.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        True if valid PDF, False otherwise
    """
    if not file_path.exists():
        return False
    
    if file_path.suffix.lower() != '.pdf':
        return False
    
    # Check PDF magic number
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except (IOError, OSError):
        return False


def format_processing_time(seconds: float) -> str:
    """
    Format processing time in human-readable format.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def estimate_processing_time(file_size_mb: float, language: str = 'english') -> float:
    """
    Estimate processing time based on file size and language.
    
    Args:
        file_size_mb: File size in megabytes
        language: Target language for processing
    
    Returns:
        Estimated processing time in seconds
    """
    # Base processing time per MB
    base_time = 2.0  # seconds per MB for English
    
    # Language complexity multipliers
    language_multipliers = {
        'english': 1.0,
        'japanese': 2.5,
        'chinese_simplified': 2.0,
        'chinese_traditional': 2.2,
        'korean': 2.3,
        'arabic': 2.1,
        'hindi': 2.0
    }
    
    multiplier = language_multipliers.get(language, 1.5)
    return file_size_mb * base_time * multiplier


class ProgressTracker:
    """Simple progress tracker for batch operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.logger = logging.getLogger(__name__)
    
    def update(self, increment: int = 1, item_name: str = ""):
        """Update progress counter."""
        self.current += increment
        percentage = (self.current / self.total) * 100
        
        status = f"{self.description}: [{self.current}/{self.total}] {percentage:.1f}%"
        if item_name:
            status += f" - {item_name}"
        
        self.logger.info(status)
    
    def finish(self, message: str = "Complete"):
        """Mark progress as finished."""
        self.logger.info(f"{self.description}: {message} ({self.total} items)")


def get_file_info(file_path: Path) -> dict:
    """
    Get basic information about a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dictionary with file information
    """
    if not file_path.exists():
        return {"error": "File not found"}
    
    stat = file_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    
    return {
        "name": file_path.name,
        "size_bytes": stat.st_size,
        "size_mb": round(size_mb, 2),
        "modified": stat.st_mtime,
        "is_valid_pdf": validate_pdf_file(file_path)
    }
