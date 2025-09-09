"""
Unit tests for the PDF parser module.
"""

import pytest
import asyncio
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from app.pdf_parser import PDFParser


class TestPDFParser:
    """Test cases for PDFParser class."""

    @pytest.fixture
    def pdf_parser(self):
        """Create a PDFParser instance for testing."""
        return PDFParser()

    def test_init(self, pdf_parser):
        """Test PDFParser initialization."""
        assert pdf_parser.supported_formats == ['.pdf', '.docx', '.txt']

    def test_get_supported_formats(self, pdf_parser):
        """Test get_supported_formats method."""
        formats = pdf_parser.get_supported_formats()
        assert formats == ['.pdf', '.docx', '.txt']
        # Ensure it returns a copy, not the original list
        formats.append('.test')
        assert pdf_parser.supported_formats == ['.pdf', '.docx', '.txt']

    @pytest.mark.asyncio
    async def test_parse_text_file_success(self, pdf_parser):
        """Test successful text file parsing."""
        test_content = "Line 1\nLine 2\nLine 3\n"
        
        with patch('aiofiles.open', mock_open(read_data=test_content)):
            with patch('os.path.getsize', return_value=len(test_content)):
                result = await pdf_parser.parse_text_file('/test/path/test.txt')
        
        assert result['format'] == 'txt'
        assert result['file_path'] == '/test/path/test.txt'
        assert len(result['text_content']) == 3
        assert result['text_content'][0]['content'] == 'Line 1'
        assert result['text_content'][1]['content'] == 'Line 2'
        assert result['metadata']['num_lines'] == 3

    @pytest.mark.asyncio
    async def test_parse_text_file_empty(self, pdf_parser):
        """Test parsing empty text file."""
        with patch('aiofiles.open', mock_open(read_data="")):
            with patch('os.path.getsize', return_value=0):
                result = await pdf_parser.parse_text_file('/test/path/empty.txt')
        
        assert result['format'] == 'txt'
        assert len(result['text_content']) == 0
        assert result['metadata']['num_lines'] == 0

    @pytest.mark.asyncio
    async def test_parse_pdf_success(self, pdf_parser):
        """Test successful PDF parsing."""
        # Mock PyPDF2 components
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {'/Title': 'Test PDF'}
        
        with patch('builtins.open', mock_open(read_data=b"fake pdf data")):
            with patch('app.pdf_parser.PdfReader', return_value=mock_reader):
                with patch('os.path.exists', return_value=True):
                    result = await pdf_parser.parse_pdf('/test/path/test.pdf')
        
        assert result['format'] == 'pdf'
        assert result['file_path'] == '/test/path/test.pdf'
        assert len(result['text_content']) == 1
        assert result['text_content'][0]['content'] == 'Test PDF content'
        assert result['metadata']['num_pages'] == 1
        assert result['metadata']['title'] == 'Test PDF'

    @pytest.mark.asyncio
    async def test_parse_pdf_file_not_found(self, pdf_parser):
        """Test PDF parsing when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                await pdf_parser.parse_pdf('/nonexistent/path/test.pdf')

    @pytest.mark.asyncio
    async def test_parse_docx_success(self, pdf_parser):
        """Test successful DOCX parsing."""
        # Mock python-docx components
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Test DOCX content"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_paragraph]
        
        with patch('app.pdf_parser.Document', return_value=mock_doc):
            result = await pdf_parser.parse_docx('/test/path/test.docx')
        
        assert result['format'] == 'docx'
        assert result['file_path'] == '/test/path/test.docx'
        assert len(result['text_content']) == 1
        assert result['text_content'][0]['content'] == 'Test DOCX content'

    @pytest.mark.asyncio
    async def test_parse_document_pdf(self, pdf_parser):
        """Test parse_document method with PDF file."""
        with patch.object(pdf_parser, 'parse_pdf') as mock_parse_pdf:
            mock_parse_pdf.return_value = {'format': 'pdf', 'content': 'test'}
            
            result = await pdf_parser.parse_document('/test/path/test.pdf')
            
            mock_parse_pdf.assert_called_once_with('/test/path/test.pdf')
            assert result['format'] == 'pdf'

    @pytest.mark.asyncio
    async def test_parse_document_txt(self, pdf_parser):
        """Test parse_document method with text file."""
        with patch.object(pdf_parser, 'parse_text_file') as mock_parse_txt:
            mock_parse_txt.return_value = {'format': 'txt', 'content': 'test'}
            
            result = await pdf_parser.parse_document('/test/path/test.txt')
            
            mock_parse_txt.assert_called_once_with('/test/path/test.txt')
            assert result['format'] == 'txt'

    @pytest.mark.asyncio
    async def test_parse_document_docx(self, pdf_parser):
        """Test parse_document method with DOCX file."""
        with patch.object(pdf_parser, 'parse_docx') as mock_parse_docx:
            mock_parse_docx.return_value = {'format': 'docx', 'content': 'test'}
            
            result = await pdf_parser.parse_document('/test/path/test.docx')
            
            mock_parse_docx.assert_called_once_with('/test/path/test.docx')
            assert result['format'] == 'docx'

    @pytest.mark.asyncio
    async def test_parse_document_unsupported_format(self, pdf_parser):
        """Test parse_document method with unsupported file format."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            await pdf_parser.parse_document('/test/path/test.xyz')

    @pytest.mark.asyncio
    async def test_parse_document_error_handling(self, pdf_parser):
        """Test error handling in parse_document method."""
        with patch.object(pdf_parser, 'parse_pdf') as mock_parse_pdf:
            mock_parse_pdf.side_effect = Exception("Test error")
            
            with pytest.raises(Exception, match="Test error"):
                await pdf_parser.parse_document('/test/path/test.pdf')


# Utility function tests
@pytest.mark.asyncio
async def test_parse_pdf_file_utility():
    """Test the utility function for parsing PDF files."""
    from app.pdf_parser import parse_pdf_file
    
    with patch('app.pdf_parser.PDFParser') as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser.parse_pdf.return_value = {'format': 'pdf', 'content': 'test'}
        mock_parser_class.return_value = mock_parser
        
        result = await parse_pdf_file('/test/path/test.pdf')
        
        mock_parser.parse_pdf.assert_called_once_with('/test/path/test.pdf')
        assert result['format'] == 'pdf'