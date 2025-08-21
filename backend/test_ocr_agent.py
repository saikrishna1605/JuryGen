"""
Simple test script for OCR Agent functionality.
"""

import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ocr_agent():
    """Test OCR agent with a simple text document."""
    try:
        from app.agents import OCRAgent
        
        # Create OCR agent
        ocr_agent = OCRAgent()
        
        # Create a simple test document
        test_content = """
        RENTAL AGREEMENT
        
        This agreement is between John Doe (Tenant) and Jane Smith (Landlord).
        
        1. RENT: The monthly rent is $1,200, due on the 1st of each month.
        
        2. SECURITY DEPOSIT: A security deposit of $1,200 is required.
        
        3. TERMINATION: Either party may terminate with 30 days notice.
        """.strip()
        
        # Test with plain text
        test_bytes = test_content.encode('utf-8')
        
        logger.info("Testing OCR agent with plain text document...")
        result = await ocr_agent.process_document(
            file_content=test_bytes,
            filename="test_rental_agreement.txt",
            content_type="text/plain"
        )
        
        logger.info(f"OCR Result:")
        logger.info(f"- Text length: {len(result.text)} characters")
        logger.info(f"- Confidence: {result.confidence}")
        logger.info(f"- Processing method: {result.processing_method}")
        logger.info(f"- Language: {result.language_code}")
        logger.info(f"- Pages: {result.layout.total_pages}")
        
        # Print first 200 characters of extracted text
        logger.info(f"- Extracted text preview: {result.text[:200]}...")
        
        logger.info("✅ OCR Agent test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ OCR Agent test failed: {str(e)}")
        return False

async def test_preprocessor():
    """Test document preprocessor functionality."""
    try:
        from app.agents import DocumentPreprocessor
        
        # Create preprocessor
        preprocessor = DocumentPreprocessor()
        
        # Test format detection
        test_content = b"This is a test document"
        
        logger.info("Testing document preprocessor...")
        
        # Test format detection
        detected_format = await preprocessor.detect_format(test_content, "test.txt")
        logger.info(f"Detected format: {detected_format}")
        
        # Test preprocessing
        processed_content, metadata = await preprocessor.preprocess_document(
            test_content, "test.txt", "text/plain"
        )
        
        logger.info(f"Preprocessing metadata: {metadata}")
        logger.info(f"Processed content length: {len(processed_content)}")
        
        # Test format info
        format_info = preprocessor.get_format_info("text/plain")
        logger.info(f"Format info: {format_info}")
        
        logger.info("✅ Document Preprocessor test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Document Preprocessor test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting OCR Agent and Preprocessor tests...")
    
    # Test preprocessor first
    preprocessor_success = await test_preprocessor()
    
    # Test OCR agent
    ocr_success = await test_ocr_agent()
    
    if preprocessor_success and ocr_success:
        logger.info("🎉 All tests passed!")
    else:
        logger.error("❌ Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())