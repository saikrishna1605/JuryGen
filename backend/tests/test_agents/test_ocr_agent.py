"""
Unit tests for OCR Agent.

Tests document OCR processing, text extraction, and layout analysis.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.ocr_agent import OCRAgent
from app.models.document import Document
from app.core.exceptions import ProcessingError


class TestOCRAgent:
    """Test cases for OCR Agent."""
    
    @pytest.fixture
    def ocr_agent(self):
        """Create OCR agent instance for testing."""
        return OCRAgent()
    
    @pytest.fixture
    def mock_document_ai_response(self):
        """Mock Document AI response."""
        mock_response = Mock()
        mock_response.document.text = "This is extracted text from the document."
        
        # Mock entities
        mock_entity = Mock()
        mock_entity.type = "PERSON"
        mock_entity.mention_text = "John Doe"
        mock_entity.confidence = 0.95
        
        mock_response.document.entities = [mock_entity]
        
        # Mock pages and blocks
        mock_page = Mock()
        mock_block = Mock()
        mock_block.layout.text_anchor.text_segments = [Mock()]
        mock_block.layout.bounding_poly.normalized_vertices = [
            Mock(x=0.1, y=0.1),
            Mock(x=0.9, y=0.9)
        ]
        
        mock_page.blocks = [mock_block]
        mock_response.document.pages = [mock_page]
        
        return mock_response
    
    @pytest.mark.asyncio
    async def test_process_document_success(
        self,
        ocr_agent,
        mock_document_ai,
        mock_document_ai_response,
        sample_document_data
    ):
        """Test successful document OCR processing."""
        # Setup
        document_id = "test-doc-123"
        file_content = b"PDF content here"
        
        # Mock Document AI client
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_client.process_document.return_value = mock_document_ai_response
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Execute
            result = await ocr_agent.process_document(document_id, file_content)
            
            # Verify
            assert result["status"] == "success"
            assert "extracted_text" in result
            assert "entities" in result
            assert "layout_analysis" in result
            assert result["extracted_text"] == "This is extracted text from the document."
            assert len(result["entities"]) == 1
            assert result["entities"][0]["type"] == "PERSON"
    
    @pytest.mark.asyncio
    async def test_process_document_with_preprocessing(
        self,
        ocr_agent,
        mock_document_ai_response
    ):
        """Test document processing with image preprocessing."""
        # Setup - simulate image content
        document_id = "test-doc-123"
        image_content = b"JPEG image content"
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_client.process_document.return_value = mock_document_ai_response
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Mock image preprocessing
            with patch.object(ocr_agent, '_preprocess_image') as mock_preprocess:
                mock_preprocess.return_value = b"preprocessed image"
                
                # Execute
                result = await ocr_agent.process_document(
                    document_id, 
                    image_content,
                    content_type="image/jpeg"
                )
                
                # Verify preprocessing was called
                mock_preprocess.assert_called_once_with(image_content)
                
                # Verify result
                assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_process_document_api_error(self, ocr_agent):
        """Test handling of Document AI API errors."""
        document_id = "test-doc-123"
        file_content = b"PDF content"
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_client.process_document.side_effect = Exception("API Error")
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Execute & Verify
            with pytest.raises(ProcessingError) as exc_info:
                await ocr_agent.process_document(document_id, file_content)
            
            assert "OCR processing failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, ocr_agent):
        """Test text extraction from PDF using fallback method."""
        # Mock PDF content
        pdf_content = b"%PDF-1.4 test content"
        
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Extracted PDF text"
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader
            
            # Execute
            result = ocr_agent._extract_text_from_pdf(pdf_content)
            
            # Verify
            assert result == "Extracted PDF text"
    
    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self, ocr_agent):
        """Test text extraction from DOCX files."""
        # Mock DOCX content
        docx_content = b"DOCX content"
        
        with patch('docx.Document') as mock_docx:
            mock_doc = Mock()
            mock_paragraph = Mock()
            mock_paragraph.text = "DOCX paragraph text"
            mock_doc.paragraphs = [mock_paragraph]
            mock_docx.return_value = mock_doc
            
            # Execute
            result = ocr_agent._extract_text_from_docx(docx_content)
            
            # Verify
            assert result == "DOCX paragraph text"
    
    @pytest.mark.asyncio
    async def test_preprocess_image_deskewing(self, ocr_agent):
        """Test image preprocessing with deskewing."""
        # Mock image content
        image_content = b"JPEG image data"
        
        with patch('PIL.Image.open') as mock_image_open:
            mock_image = Mock()
            mock_image.rotate.return_value = mock_image
            mock_image.save = Mock()
            mock_image_open.return_value = mock_image
            
            with patch('cv2.imread') as mock_cv2_imread:
                mock_cv2_imread.return_value = Mock()
                
                with patch.object(ocr_agent, '_detect_skew_angle') as mock_detect_skew:
                    mock_detect_skew.return_value = 5.0  # 5 degree skew
                    
                    # Execute
                    result = ocr_agent._preprocess_image(image_content)
                    
                    # Verify deskewing was applied
                    mock_image.rotate.assert_called_once_with(-5.0, expand=True)
                    assert isinstance(result, bytes)
    
    @pytest.mark.asyncio
    async def test_detect_skew_angle(self, ocr_agent):
        """Test skew angle detection."""
        # Mock OpenCV operations
        with patch('cv2.cvtColor') as mock_cvt_color:
            with patch('cv2.Canny') as mock_canny:
                with patch('cv2.HoughLines') as mock_hough_lines:
                    # Mock detected lines
                    mock_hough_lines.return_value = [
                        [[100, 0.1]],  # rho, theta
                        [[200, 0.15]]
                    ]
                    
                    mock_image = Mock()
                    
                    # Execute
                    angle = ocr_agent._detect_skew_angle(mock_image)
                    
                    # Verify
                    assert isinstance(angle, float)
                    assert -45 <= angle <= 45  # Reasonable angle range
    
    @pytest.mark.asyncio
    async def test_enhance_image_quality(self, ocr_agent):
        """Test image quality enhancement."""
        with patch('cv2.imread') as mock_imread:
            with patch('cv2.GaussianBlur') as mock_blur:
                with patch('cv2.addWeighted') as mock_add_weighted:
                    with patch('cv2.threshold') as mock_threshold:
                        mock_image = Mock()
                        mock_imread.return_value = mock_image
                        mock_blur.return_value = mock_image
                        mock_add_weighted.return_value = mock_image
                        mock_threshold.return_value = (None, mock_image)
                        
                        # Execute
                        result = ocr_agent._enhance_image_quality(b"image data")
                        
                        # Verify enhancement steps were called
                        mock_blur.assert_called()
                        mock_add_weighted.assert_called()
                        mock_threshold.assert_called()
    
    @pytest.mark.asyncio
    async def test_extract_layout_information(
        self,
        ocr_agent,
        mock_document_ai_response
    ):
        """Test layout information extraction."""
        # Execute
        layout_info = ocr_agent._extract_layout_information(mock_document_ai_response.document)
        
        # Verify
        assert "pages" in layout_info
        assert "blocks" in layout_info
        assert len(layout_info["pages"]) == 1
        assert len(layout_info["blocks"]) == 1
        
        block = layout_info["blocks"][0]
        assert "bounding_box" in block
        assert "page" in block
    
    @pytest.mark.asyncio
    async def test_extract_entities(
        self,
        ocr_agent,
        mock_document_ai_response
    ):
        """Test entity extraction from Document AI response."""
        # Execute
        entities = ocr_agent._extract_entities(mock_document_ai_response.document)
        
        # Verify
        assert len(entities) == 1
        entity = entities[0]
        assert entity["type"] == "PERSON"
        assert entity["text"] == "John Doe"
        assert entity["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, ocr_agent):
        """Test OCR confidence scoring."""
        # Mock document with confidence scores
        mock_document = Mock()
        mock_page = Mock()
        mock_block = Mock()
        mock_paragraph = Mock()
        mock_word = Mock()
        
        # Set up confidence hierarchy
        mock_word.layout.confidence = 0.9
        mock_paragraph.words = [mock_word]
        mock_paragraph.layout.confidence = 0.85
        mock_block.paragraphs = [mock_paragraph]
        mock_block.layout.confidence = 0.8
        mock_page.blocks = [mock_block]
        mock_page.layout.confidence = 0.75
        mock_document.pages = [mock_page]
        
        # Execute
        confidence = ocr_agent._calculate_overall_confidence(mock_document)
        
        # Verify
        assert 0 <= confidence <= 1
        assert confidence > 0.7  # Should be reasonably high
    
    @pytest.mark.asyncio
    async def test_fallback_to_vision_api(self, ocr_agent):
        """Test fallback to Vision API when Document AI fails."""
        document_id = "test-doc-123"
        image_content = b"JPEG image"
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            # Mock Document AI failure
            mock_client = Mock()
            mock_client.process_document.side_effect = Exception("Document AI failed")
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Mock Vision API success
            with patch('google.cloud.vision.ImageAnnotatorClient') as mock_vision:
                mock_vision_client = Mock()
                mock_response = Mock()
                mock_response.full_text_annotation.text = "Vision API extracted text"
                mock_vision_client.text_detection.return_value = mock_response
                mock_vision.return_value = mock_vision_client
                
                # Execute
                result = await ocr_agent.process_document(
                    document_id,
                    image_content,
                    content_type="image/jpeg"
                )
                
                # Verify fallback was used
                assert result["status"] == "success"
                assert result["extracted_text"] == "Vision API extracted text"
                assert result["fallback_used"] is True
    
    @pytest.mark.asyncio
    async def test_performance_tracking(
        self,
        ocr_agent,
        mock_document_ai_response,
        mock_monitoring
    ):
        """Test performance metrics tracking."""
        document_id = "test-doc-123"
        file_content = b"PDF content"
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_client.process_document.return_value = mock_document_ai_response
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Execute
            result = await ocr_agent.process_document(document_id, file_content)
            
            # Verify performance metrics were recorded
            assert mock_monitoring['record_metric'].called
            
            # Check that processing time was recorded
            metric_calls = mock_monitoring['record_metric'].call_args_list
            processing_time_recorded = any(
                'processing_duration' in str(call) for call in metric_calls
            )
            assert processing_time_recorded
    
    @pytest.mark.asyncio
    async def test_large_document_handling(self, ocr_agent):
        """Test handling of large documents."""
        document_id = "test-large-doc"
        # Simulate large document (10MB)
        large_content = b"x" * (10 * 1024 * 1024)
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.document.text = "Large document text"
            mock_response.document.entities = []
            mock_response.document.pages = []
            mock_client.process_document.return_value = mock_response
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Execute
            result = await ocr_agent.process_document(document_id, large_content)
            
            # Verify successful processing
            assert result["status"] == "success"
            assert "processing_time" in result
    
    @pytest.mark.asyncio
    async def test_multi_page_document(
        self,
        ocr_agent,
        mock_document_ai_response
    ):
        """Test processing of multi-page documents."""
        # Modify mock response for multi-page
        mock_page_1 = Mock()
        mock_page_2 = Mock()
        mock_document_ai_response.document.pages = [mock_page_1, mock_page_2]
        mock_document_ai_response.document.text = "Page 1 text\nPage 2 text"
        
        document_id = "test-multipage-doc"
        file_content = b"Multi-page PDF content"
        
        with patch('app.agents.ocr_agent.documentai') as mock_documentai:
            mock_client = Mock()
            mock_client.process_document.return_value = mock_document_ai_response
            mock_documentai.DocumentProcessorServiceClient.return_value = mock_client
            
            # Execute
            result = await ocr_agent.process_document(document_id, file_content)
            
            # Verify
            assert result["status"] == "success"
            assert result["layout_analysis"]["pages"] == 2
            assert "Page 1 text" in result["extracted_text"]
            assert "Page 2 text" in result["extracted_text"]