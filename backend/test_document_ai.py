#!/usr/bin/env python3
"""
Test script to verify Document AI Custom Extractor setup.
"""

import os
import asyncio
from app.agents.ocr_agent import OCRAgent

async def test_document_ai():
    """Test Document AI configuration."""
    
    # Check environment variables
    processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
    location = os.getenv('DOCUMENT_AI_LOCATION')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    print(f"Project ID: {project_id}")
    print(f"Location: {location}")
    print(f"Processor ID: {processor_id}")
    
    if processor_id == 'your-processor-id-here':
        print("❌ Please update DOCUMENT_AI_PROCESSOR_ID in your .env file")
        return
    
    # Initialize OCR agent
    try:
        ocr_agent = OCRAgent()
        print("✅ OCR Agent initialized successfully")
        
        if ocr_agent.doc_ai_client:
            print("✅ Document AI client connected")
        else:
            print("⚠️  Document AI client not available - check credentials")
            
    except Exception as e:
        print(f"❌ Error initializing OCR Agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_document_ai())