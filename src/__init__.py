"""
PDF Outline Extractor - A modular OCR-based PDF outline extraction tool.

This package provides tools for extracting structured outlines from PDF files
using both direct text extraction and OCR with multilingual support.
"""

__version__ = "1.0.0"
__author__ = "PDF Outline Extractor Team"

from .extractor import OptimizedOCRExtractor
from .processor import BatchProcessor
from .config import Config
from .utils import setup_logging

__all__ = [
    'OptimizedOCRExtractor',
    'BatchProcessor', 
    'Config',
    'setup_logging'
]
