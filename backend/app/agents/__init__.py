"""
AI Agents for legal document processing.

This module contains specialized agents for different aspects of legal document analysis:
- OCR Agent: Document digitization and text extraction
- Document Preprocessor: Document format detection and preprocessing utilities
- Clause Analyzer: Legal clause classification and risk assessment
- Summarizer: Plain language document summaries
- Risk Advisor: Risk assessment and safer alternatives
- Translator: Multi-language support
"""

from .ocr_agent import OCRAgent
from .preprocessing import DocumentPreprocessor

__all__ = ["OCRAgent", "DocumentPreprocessor"]