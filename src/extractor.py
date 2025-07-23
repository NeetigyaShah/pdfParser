"""
OCR-based text extraction module with multilingual support.
Handles both direct text extraction and OCR processing for various languages.
"""

import fitz
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import io
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from .config import Config
from .utils import format_processing_time


logger = logging.getLogger(__name__)


class OptimizedOCRExtractor:
    """Optimized OCR-based text extractor with multilingual support."""
    
    def __init__(self, language: str = 'english', auto_detect_language: bool = True):
        """
        Initialize the OCR extractor.
        
        Args:
            language: Target language for OCR processing
            auto_detect_language: Whether to auto-detect language from PDF content
        """
        self.config = Config(language)
        self.auto_detect_language = auto_detect_language
        self.detected_language = None
        
        logger.info(f"Initialized OCR extractor for language: {language}")
        logger.info(f"Tesseract language code: {self.config.tesseract_lang}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Optimized image preprocessing for better OCR across languages.
        
        Args:
            image: Input image as numpy array
        
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise - important for Asian languages
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Improve contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # For Asian languages, use different thresholding
        if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean']:
            # Use Otsu's thresholding for better Asian character recognition
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            # Adaptive threshold for Latin-based languages
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        
        # Morphological operations to clean up
        kernel_size = (2, 2) if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional'] else (1, 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_with_positions(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with position and formatting information.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of text lines with metadata
        """
        doc = fitz.open(pdf_path)
        all_lines = []
        
        # Auto-detect language if enabled
        if self.auto_detect_language and not self.detected_language:
            self._detect_document_language(doc)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Try direct text extraction first
            text_dict = page.get_text("dict")
            has_text = any(
                block.get("lines") for block in text_dict.get("blocks", [])
                if "lines" in block
            )
            
            if has_text:
                lines = self._extract_direct_text(page, page_num)
                all_lines.extend(lines)
            else:
                lines = self._extract_ocr_text(page, page_num)
                all_lines.extend(lines)
        
        doc.close()
        return all_lines
    
    def _detect_document_language(self, doc) -> None:
        """
        Detect the primary language of the document.
        
        Args:
            doc: PyMuPDF document object
        """
        sample_text = ""
        
        # Extract sample text from first few pages
        for page_num in range(min(3, doc.page_count)):
            page = doc[page_num]
            text = page.get_text()
            sample_text += text[:1000]  # First 1000 chars per page
            
            if len(sample_text) > 2000:  # Enough sample
                break
        
        if sample_text:
            detected = Config.detect_language(sample_text)
            if detected != self.config.language:
                logger.info(f"Auto-detected language: {detected} (configured: {self.config.language})")
                self.detected_language = detected
                # Update config for detected language
                self.config = Config(detected)
    
    def _extract_direct_text(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text directly with formatting information.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
        
        Returns:
            List of text lines with metadata
        """
        lines = []
        text_dict = page.get_text("dict")
        page_width = page.rect.width
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    max_font_size = 0
                    is_bold = False
                    x_pos = float('inf')
                    y_pos = 0
                    
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            line_text += text + " "
                            max_font_size = max(max_font_size, span["size"])
                            if span["flags"] & 2**4:  # Bold flag
                                is_bold = True
                            x_pos = min(x_pos, span["bbox"][0])
                            y_pos = span["bbox"][1]
                    
                    line_text = line_text.strip()
                    if line_text and len(line_text) > 1:  # More lenient for Asian languages
                        is_centered = self._is_text_centered(x_pos, page_width)
                        
                        lines.append({
                            "text": line_text,
                            "page": page_num,
                            "font_size": max_font_size,
                            "is_bold": is_bold,
                            "x": x_pos,
                            "y": y_pos,
                            "is_centered": is_centered,
                            "method": "direct"
                        })
        
        return lines
    
    def _extract_ocr_text(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text using OCR with language-specific settings.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
        
        Returns:
            List of text lines with metadata
        """
        # Convert page to high-resolution image
        # Higher resolution for Asian languages
        zoom_factor = 4 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 3
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Convert to PIL then OpenCV
        pil_img = Image.open(io.BytesIO(img_data))
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Preprocess for better OCR
        processed_img = self.preprocess_image(cv_img)
        
        # Get OCR data with language-specific configuration
        try:
            ocr_config = self.config.get_ocr_config()
            ocr_data = pytesseract.image_to_data(
                processed_img,
                config=ocr_config,
                output_type=pytesseract.Output.DICT
            )
        except Exception as e:
            logger.warning(f"OCR failed for page {page_num}: {e}")
            return []
        
        # Group words into lines
        lines = self._group_words_into_lines(ocr_data, page_num, page.rect.width, zoom_factor)
        
        # Fallback: if no lines detected, try simpler OCR
        if not lines:
            try:
                raw_text = pytesseract.image_to_string(processed_img, config=ocr_config)
                fallback = []
                for ln in raw_text.splitlines():
                    ln = ln.strip()
                    if len(ln) > 1:  # More lenient for all languages
                        fallback.append({
                            "text": ln,
                            "page": page_num,
                            "font_size": 12,
                            "is_bold": False,
                            "x": 0,
                            "y": 0,
                            "is_centered": False,
                            "method": "ocr_fallback"
                        })
                return fallback
            except Exception as e:
                logger.error(f"Fallback OCR also failed for page {page_num}: {e}")
                return []
        
        return lines
    
    def _group_words_into_lines(self, ocr_data: dict, page_num: int, page_width: float, zoom_factor: int) -> List[Dict[str, Any]]:
        """
        Group OCR words into coherent lines with language-aware spacing.
        
        Args:
            ocr_data: Tesseract OCR output data
            page_num: Page number (0-based)
            page_width: Width of the page
            zoom_factor: Image zoom factor used
        
        Returns:
            List of grouped text lines
        """
        lines = []
        current_line = {"words": [], "bbox": None, "confidences": []}
        
        # Lower confidence threshold for Asian languages
        min_confidence = 20 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 30
        
        for i in range(len(ocr_data["text"])):
            word = ocr_data["text"][i].strip()
            conf = int(ocr_data["conf"][i])
            
            if word and conf > min_confidence:
                x = ocr_data["left"][i] // zoom_factor
                y = ocr_data["top"][i] // zoom_factor
                w = ocr_data["width"][i] // zoom_factor
                h = ocr_data["height"][i] // zoom_factor
                
                # More tolerant y-position for line grouping with Asian languages
                y_tolerance = 15 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 12
                
                if (not current_line["bbox"] or 
                    abs(y - current_line["bbox"][1]) < y_tolerance):
                    
                    current_line["words"].append(word)
                    current_line["confidences"].append(conf)
                    
                    if current_line["bbox"] is None:
                        current_line["bbox"] = [x, y, w, h]
                    else:
                        # Extend bounding box
                        old_bbox = current_line["bbox"]
                        new_right = max(old_bbox[0] + old_bbox[2], x + w)
                        current_line["bbox"][2] = new_right - old_bbox[0]
                        current_line["bbox"][3] = max(old_bbox[3], h)
                else:
                    # Finalize current line and start new one
                    if current_line["words"]:
                        line_info = self._finalize_line(current_line, page_num, page_width)
                        if line_info:
                            lines.append(line_info)
                    
                    current_line = {
                        "words": [word],
                        "bbox": [x, y, w, h],
                        "confidences": [conf]
                    }
        
        # Add final line
        if current_line["words"]:
            line_info = self._finalize_line(current_line, page_num, page_width)
            if line_info:
                lines.append(line_info)
        
        return lines
    
    def _finalize_line(self, line_data: dict, page_num: int, page_width: float) -> Optional[Dict[str, Any]]:
        """
        Convert line data to final format with language-aware processing.
        
        Args:
            line_data: Raw line data from OCR
            page_num: Page number (0-based)
            page_width: Width of the page
        
        Returns:
            Finalized line information or None if invalid
        """
        # For Asian languages, don't add spaces between words
        if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional']:
            text = "".join(line_data["words"])
        else:
            text = " ".join(line_data["words"])
        
        avg_confidence = sum(line_data["confidences"]) / len(line_data["confidences"])
        
        # More permissive quality threshold
        min_length = 1 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 2
        min_conf = 20 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 25
        
        if len(text) < min_length or avg_confidence < min_conf:
            return None
        
        bbox = line_data["bbox"]
        font_size = self._estimate_font_size(bbox[3])
        is_bold = self._detect_bold_text(text, font_size)
        is_centered = self._is_text_centered(bbox[0], page_width)
        
        return {
            "text": text,
            "page": page_num,
            "font_size": font_size,
            "is_bold": is_bold,
            "x": bbox[0],
            "y": bbox[1],
            "is_centered": is_centered,
            "confidence": avg_confidence,
            "method": "ocr"
        }
    
    def _estimate_font_size(self, height: int) -> float:
        """Estimate font size from text height."""
        return max(8, min(28, height * 0.8))
    
    def _detect_bold_text(self, text: str, font_size: float) -> bool:
        """
        Detect if text is likely bold based on patterns and language.
        
        Args:
            text: Text content
            font_size: Estimated font size
        
        Returns:
            True if likely bold text
        """
        # Check heading patterns
        for pattern, _, _ in self.config.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Large font size suggests heading
        if font_size > 14:
            return True
        
        # Language-specific bold detection
        if self.config.language == 'english':
            if text.isupper() and len(text) > 3:
                return True
        
        return False
    
    def _is_text_centered(self, x_pos: float, page_width: float) -> bool:
        """
        Check if text appears to be centered.
        
        Args:
            x_pos: X position of text
            page_width: Width of the page
        
        Returns:
            True if text appears centered
        """
        center_zone = page_width * 0.3  # 30% zone around center
        page_center = page_width / 2
        return abs(x_pos - page_center) < center_zone
    
    def classify_heading(self, line: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classify line as heading type with confidence score.
        
        Args:
            line: Line data with text and metadata
        
        Returns:
            Tuple of (heading_type, confidence)
        """
        text = line["text"].strip()
        font_size = line.get("font_size", 12)
        is_bold = line.get("is_bold", False)
        is_centered = line.get("is_centered", False)
        method = line.get("method", "direct")
        
        # Skip very short text (more lenient for Asian languages)
        min_length = 1 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 3
        if len(text) < min_length:
            return "BODY", 0.1
        
        # Skip numeric-only text
        if re.match(r'^[\d\s]+$', text):
            return "BODY", 0.1
        
        # Pattern-based classification
        best_match = ("BODY", 0.0)
        
        for pattern, heading_type, base_confidence in self.config.heading_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                confidence = base_confidence
                
                # Boost confidence based on formatting
                if is_bold:
                    confidence += 0.1
                if font_size >= self.config.font_thresholds.get(heading_type, 12):
                    confidence += 0.15
                if is_centered and heading_type == "TITLE":
                    confidence += 0.2
                if method == "direct":
                    confidence += 0.05
                
                confidence = min(0.98, confidence)
                
                if confidence > best_match[1]:
                    best_match = (heading_type, confidence)
        
        # Fallback formatting-based classification
        if best_match[1] < 0.25:
            if font_size >= 18 and (is_bold or is_centered):
                best_match = ("TITLE", 0.5)
            elif font_size >= 16 and is_bold:
                best_match = ("H1", 0.4)
            elif font_size >= 14 and is_bold:
                best_match = ("H2", 0.35)
            elif font_size >= 12 and is_bold:
                best_match = ("H3", 0.25)
            elif is_centered and len(text) > 8:
                best_match = ("TITLE", 0.3)
        
        return best_match
    
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract complete outline from PDF with multilingual support.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Dictionary with title, outline, and statistics
        """
        start_time = time.time()
        
        logger.info(f"Extracting outline from: {Path(pdf_path).name}")
        logger.info(f"Language: {self.config.language} ({self.config.tesseract_lang})")
        
        # Extract all text lines
        lines = self.extract_text_with_positions(pdf_path)
        
        # Classify lines and build outline
        outline_items = []
        title = ""
        
        for line in lines:
            heading_type, confidence = self.classify_heading(line)
            
            # Lower confidence threshold for multilingual support
            min_confidence = 0.2 if self.config.language in ['japanese', 'chinese_simplified', 'chinese_traditional', 'korean'] else 0.25
            
            if heading_type != "BODY" and confidence > min_confidence:
                # Handle title extraction
                if heading_type == "TITLE":
                    if not title:
                        title = line["text"]
                        continue
                    else:
                        heading_type = "H1"  # Convert subsequent titles to H1
                
                outline_item = {
                    "level": heading_type,
                    "text": line["text"],
                    "page": line["page"] + 1  # 1-based page numbering
                }
                outline_items.append(outline_item)
                
                # Extract title from first significant heading if not found
                if not title and heading_type == "H1" and confidence > 0.5:
                    title = line["text"]
        
        # If no title found, use filename or first heading
        if not title:
            if outline_items:
                title = outline_items[0]["text"]
            else:
                title = Path(pdf_path).stem
        
        processing_time = time.time() - start_time
        
        logger.info(f"Extraction complete: {len(outline_items)} headings found in {format_processing_time(processing_time)}")
        
        return {
            "title": title,
            "outline": outline_items,
            "_stats": {
                "processing_time": processing_time,
                "total_lines": len(lines),
                "headings_found": len(outline_items),
                "language": self.config.language,
                "detected_language": self.detected_language
            }
        }
