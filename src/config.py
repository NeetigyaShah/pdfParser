"""
Configuration module for PDF Outline Extractor.
Handles language support, OCR settings, and application configuration.
"""

import os
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LanguageConfig:
    """Configuration for specific language support."""
    tesseract_lang: str
    patterns: List[Tuple[str, str, float]]
    font_thresholds: Dict[str, int]
    char_whitelist: str


class Config:
    """Main configuration class with multilingual support."""
    
    # Supported languages with their Tesseract language codes
    SUPPORTED_LANGUAGES = {
        'english': 'eng',
        'japanese': 'jpn',
        'chinese_simplified': 'chi_sim',
        'chinese_traditional': 'chi_tra',
        'korean': 'kor',
        'spanish': 'spa',
        'french': 'fra',
        'german': 'deu',
        'portuguese': 'por',
        'italian': 'ita',
        'russian': 'rus',
        'arabic': 'ara',
        'hindi': 'hin'
    }
    
    def __init__(self, language: str = 'english'):
        """Initialize configuration for specified language."""
        self.language = language.lower()
        if self.language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}. Supported: {list(self.SUPPORTED_LANGUAGES.keys())}")
        
        self.tesseract_lang = self.SUPPORTED_LANGUAGES[self.language]
        self.config = self._get_language_config()
    
    def _get_language_config(self) -> LanguageConfig:
        """Get language-specific configuration."""
        if self.language == 'english':
            return self._get_english_config()
        elif self.language == 'japanese':
            return self._get_japanese_config()
        elif self.language in ['chinese_simplified', 'chinese_traditional']:
            return self._get_chinese_config()
        elif self.language == 'korean':
            return self._get_korean_config()
        else:
            # Default to English patterns with language-specific Tesseract
            return self._get_default_config()
    
    def _get_english_config(self) -> LanguageConfig:
        """English language configuration."""
        patterns = [
            # Chapter patterns (highest priority)
            (r'^(Chapter|CHAPTER)\s+(\d+|[IVX]+)[:.]?\s*(.+)', 'H1', 0.9),
            (r'^([IVX]+\.)\s+(.+)', 'H1', 0.85),
            (r'^(\d+\.)\s+([A-Z].*)', 'H1', 0.8),
            
            # Section patterns
            (r'^(\d+\.\d+)\s+(.+)', 'H2', 0.8),
            (r'^([A-Z]\.|[a-z]\.)\s+(.+)', 'H2', 0.7),
            (r'^(\d+\.\d+\.\d+)\s+(.+)', 'H3', 0.75),
            
            # Subsection patterns
            (r'^([a-z]\)|[A-Z]\)|\d+\))\s+(.+)', 'H3', 0.6),
            (r'^(•|\*|-|\+)\s+(.+)', 'H3', 0.5),
            
            # Title patterns (ALL CAPS, centered)
            (r'^[A-Z\s\d]{8,}$', 'TITLE', 0.7),
            (r'^[A-Z][A-Z\s\d:,-]{10,}$', 'TITLE', 0.6),
            
            # Content-based patterns
            (r'\b(education|experience|projects|skills|technical|summary|objective)\b', 'H1', 0.6),
            (r'\b(introduction|overview|conclusion|abstract)\b', 'H1', 0.5),
        ]
        
        font_thresholds = {'TITLE': 16, 'H1': 14, 'H2': 12, 'H3': 10}
        
        char_whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?:;()[]{}/-\'"@ '
        
        return LanguageConfig(
            tesseract_lang='eng',
            patterns=patterns,
            font_thresholds=font_thresholds,
            char_whitelist=char_whitelist
        )
    
    def _get_japanese_config(self) -> LanguageConfig:
        """Japanese language configuration."""
        patterns = [
            # Japanese chapter patterns
            (r'^(第|だい)[0-9０-９一二三四五六七八九十百]+[章節][:：]?\s*(.+)', 'H1', 0.9),
            (r'^[0-9０-９]+[\.．]\s*(.+)', 'H1', 0.8),
            (r'^[0-9０-９]+[\.．][0-9０-９]+[\.．]\s*(.+)', 'H2', 0.8),
            (r'^[0-9０-９]+[\.．][0-9０-９]+[\.．][0-9０-９]+[\.．]\s*(.+)', 'H3', 0.75),
            
            # Japanese bullet points
            (r'^[・●○◎◆▲■□△▽▼▶◀▮☆★※]\s*(.+)', 'H3', 0.6),
            (r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*(.+)', 'H3', 0.6),
            
            # Common Japanese headings
            (r'^(目次|もくじ|概要|がいよう|はじめに|終わりに|まとめ|結論|けつろん)', 'H1', 0.8),
            (r'^(序論|本論|結論|序文|まえがき|あとがき)', 'H1', 0.7),
            (r'^(背景|目的|方法|結果|考察|参考文献)', 'H1', 0.6),
            
            # Title patterns for Japanese
            (r'^[ァ-ヶー一-龯]{8,}$', 'TITLE', 0.6),
        ]
        
        font_thresholds = {'TITLE': 16, 'H1': 14, 'H2': 12, 'H3': 10}
        
        # Japanese character set (basic)
        char_whitelist = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん' + \
                        'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン' + \
                        '一二三四五六七八九十百千万億兆' + \
                        '0123456789０１２３４５６７８９' + \
                        '.,!?:;()[]{}/-\'"@・ー～｜「」『』【】〈〉《》〔〕（）｛｝ '
        
        return LanguageConfig(
            tesseract_lang='jpn',
            patterns=patterns,
            font_thresholds=font_thresholds,
            char_whitelist=char_whitelist
        )
    
    def _get_chinese_config(self) -> LanguageConfig:
        """Chinese language configuration."""
        patterns = [
            # Chinese chapter patterns
            (r'^第[0-9一二三四五六七八九十百千万]+[章节部分]\s*(.+)', 'H1', 0.9),
            (r'^[0-9]+[\.．]\s*(.+)', 'H1', 0.8),
            (r'^[0-9]+[\.．][0-9]+[\.．]\s*(.+)', 'H2', 0.8),
            
            # Chinese bullet points
            (r'^[·•○●◎◆▲■□△▽▼]\s*(.+)', 'H3', 0.6),
            
            # Common Chinese headings
            (r'^(目录|概述|概要|前言|序言|结论|总结|参考文献)', 'H1', 0.8),
            (r'^(背景|目的|方法|结果|讨论|分析)', 'H1', 0.6),
        ]
        
        font_thresholds = {'TITLE': 16, 'H1': 14, 'H2': 12, 'H3': 10}
        
        # Chinese characters and common punctuation
        char_whitelist = '一二三四五六七八九十百千万亿' + \
                        '0123456789' + \
                        '.,!?:;()[]{}/-\'"@·～｜「」『』【】〈〉《》〔〕（）｛｝ '
        
        tesseract_lang = 'chi_sim' if self.language == 'chinese_simplified' else 'chi_tra'
        
        return LanguageConfig(
            tesseract_lang=tesseract_lang,
            patterns=patterns,
            font_thresholds=font_thresholds,
            char_whitelist=char_whitelist
        )
    
    def _get_korean_config(self) -> LanguageConfig:
        """Korean language configuration."""
        patterns = [
            # Korean chapter patterns
            (r'^제[0-9]+[장절부]\s*(.+)', 'H1', 0.9),
            (r'^[0-9]+[\.]\s*(.+)', 'H1', 0.8),
            (r'^[0-9]+[\.][0-9]+[\.]\s*(.+)', 'H2', 0.8),
            
            # Korean bullet points
            (r'^[·•○●◎◆▲■□△▽▼]\s*(.+)', 'H3', 0.6),
            
            # Common Korean headings
            (r'^(목차|개요|서론|결론|요약|참고문헌)', 'H1', 0.8),
            (r'^(배경|목적|방법|결과|논의|분석)', 'H1', 0.6),
        ]
        
        font_thresholds = {'TITLE': 16, 'H1': 14, 'H2': 12, 'H3': 10}
        
        # Korean Hangul and common characters
        char_whitelist = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ가나다라마바사아자차카타파하' + \
                        '0123456789' + \
                        '.,!?:;()[]{}/-\'"@ '
        
        return LanguageConfig(
            tesseract_lang='kor',
            patterns=patterns,
            font_thresholds=font_thresholds,
            char_whitelist=char_whitelist
        )
    
    def _get_default_config(self) -> LanguageConfig:
        """Default configuration for unsupported languages."""
        # Use English patterns but with the appropriate Tesseract language
        english_config = self._get_english_config()
        english_config.tesseract_lang = self.tesseract_lang
        return english_config
    
    def get_ocr_config(self) -> str:
        """Get Tesseract OCR configuration string."""
        base_config = f'--oem 3 --psm 6 -l {self.config.tesseract_lang}'
        
        # Add character whitelist if specified
        if self.config.char_whitelist:
            whitelist = self.config.char_whitelist.replace(' ', '\\s')
            base_config += f' -c tessedit_char_whitelist={whitelist}'
        
        return base_config
    
    @property
    def heading_patterns(self) -> List[Tuple[str, str, float]]:
        """Get heading patterns for current language."""
        return self.config.patterns
    
    @property
    def font_thresholds(self) -> Dict[str, int]:
        """Get font size thresholds for current language."""
        return self.config.font_thresholds
    
    @classmethod
    def detect_language(cls, text_sample: str) -> str:
        """Attempt to detect language from text sample."""
        # Simple heuristic-based language detection
        japanese_chars = len([c for c in text_sample if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF'])
        chinese_chars = len([c for c in text_sample if '\u4E00' <= c <= '\u9FAF'])
        korean_chars = len([c for c in text_sample if '\uAC00' <= c <= '\uD7AF'])
        
        total_chars = len([c for c in text_sample if c.isalpha()])
        
        if total_chars > 0:
            if japanese_chars / total_chars > 0.3:
                return 'japanese'
            elif korean_chars / total_chars > 0.3:
                return 'korean'
            elif chinese_chars / total_chars > 0.3:
                return 'chinese_simplified'  # Default to simplified
        
        return 'english'  # Default fallback
