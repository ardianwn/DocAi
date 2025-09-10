"""
Unit tests for the RAG service module.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.rag_service import RAGService


class TestRAGService:
    """Test cases for RAGService class."""

    @pytest.fixture
    def rag_service(self, mock_llm_client, mock_embedding_client, mock_vector_store, mock_document_parser):
        """Create a RAGService instance with mocked dependencies."""
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'mock',
            'EMBEDDING_PROVIDER': 'mock',
            'QDRANT_HOST': 'mock',
            'COLLECTION_NAME': 'test_collection'
        }):
            service = RAGService()
            service.llm_client = mock_llm_client
            service.embedding_client = mock_embedding_client
            service.vector_store = mock_vector_store
            service.document_parser = mock_document_parser
            return service

    @pytest.mark.asyncio
    async def test_initialize_success(self, rag_service):
        """Test successful RAG service initialization."""
        result = await rag_service.initialize()
        assert result is True
        rag_service.vector_store.create_collection.assert_called_once()
        rag_service.vector_store.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_vector_store_failure(self, rag_service):
        """Test initialization failure when vector store is unhealthy."""
        rag_service.vector_store.health_check.return_value = False
        
        result = await rag_service.initialize()
        assert result is False

    @pytest.mark.asyncio
    async def test_process_document_success(self, rag_service):
        """Test successful document processing."""
        # Setup mocks
        rag_service.document_parser.parse_document.return_value = {
            "text_content": [
                {"content": "Test content 1", "page": 1},
                {"content": "Test content 2", "page": 2}
            ],
            "metadata": {"num_pages": 2},
            "file_path": "/test/path/test.pdf",
            "format": "pdf"
        }
        
        rag_service.embedding_client.embed_documents.return_value = [
            {
                "content": "Test content 1",
                "embedding": [0.1] * 768,
                "has_embedding": True,
                "embedding_model": "test-model"
            },
            {
                "content": "Test content 2",
                "embedding": [0.2] * 768,
                "has_embedding": True,
                "embedding_model": "test-model"
            }
        ]
        
        rag_service.vector_store.upsert_documents.return_value = True
        
        result = await rag_service.process_document("/test/path/test.pdf", "test.pdf")
        
        assert result["success"] is True
        assert result["filename"] == "test.pdf"
        assert result["chunks_processed"] == 2
        assert result["chunks_embedded"] == 2
        
        # Verify method calls
        rag_service.document_parser.parse_document.assert_called_once_with("/test/path/test.pdf")
        rag_service.embedding_client.embed_documents.assert_called_once()
        rag_service.vector_store.upsert_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_parse_failure(self, rag_service):
        """Test document processing when parsing fails."""
        rag_service.document_parser.parse_document.return_value = None
        
        result = await rag_service.process_document("/test/path/test.pdf", "test.pdf")
        
        assert result["success"] is False
        assert "Failed to extract text" in result["error"]

    @pytest.mark.asyncio
    async def test_process_document_no_embeddings(self, rag_service):
        """Test document processing when embedding generation fails."""
        rag_service.document_parser.parse_document.return_value = {
            "text_content": [{"content": "Test content", "page": 1}],
            "metadata": {"num_pages": 1},
            "file_path": "/test/path/test.pdf",
            "format": "pdf"
        }
        
        rag_service.embedding_client.embed_documents.return_value = [
            {
                "content": "Test content",
                "embedding": None,
                "has_embedding": False,
                "embedding_model": "test-model"
            }
        ]
        
        result = await rag_service.process_document("/test/path/test.pdf", "test.pdf")
        
        assert result["success"] is False
        assert "Failed to generate embeddings" in result["error"]

    @pytest.mark.asyncio
    async def test_chat_with_documents_success(self, rag_service):
        """Test successful chat with documents."""
        # Setup mocks
        rag_service.embedding_client.generate_embedding.return_value = [0.1] * 768
        
        rag_service.vector_store.search_similar.return_value = [
            {
                "id": "test-doc-1",
                "score": 0.9,
                "content": "test content",
                "source": "test.pdf",
                "page": 1
            }
        ]
        
        rag_service.llm_client.chat_with_documents.return_value = {
            "question": "What is this about?",
            "answer": "This is about testing.",
            "sources": [],
            "error": False
        }
        
        result = await rag_service.chat_with_documents("What is this about?", "test-session")
        
        assert result["question"] == "What is this about?"
        assert result["answer"] == "This is about testing."
        assert result["error"] is False
        
        # Verify method calls
        rag_service.embedding_client.generate_embedding.assert_called_once_with("What is this about?")
        rag_service.vector_store.search_similar.assert_called_once()
        rag_service.llm_client.chat_with_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_documents_no_embedding(self, rag_service):
        """Test chat when question embedding generation fails."""
        rag_service.embedding_client.generate_embedding.return_value = None
        
        result = await rag_service.chat_with_documents("What is this about?", "test-session")
        
        assert result["error"] is True
        assert "couldn't process your question" in result["answer"]

    @pytest.mark.asyncio
    async def test_chat_with_documents_llm_fallback(self, rag_service):
        """Test chat when LLM client doesn't have chat_with_documents method."""
        # Remove the chat_with_documents method to trigger fallback
        delattr(rag_service.llm_client, 'chat_with_documents')
        
        rag_service.embedding_client.generate_embedding.return_value = [0.1] * 768
        rag_service.vector_store.search_similar.return_value = []
        
        rag_service.llm_client.generate_response.return_value = {
            "question": "What is this about?",
            "answer": "This is a fallback response.",
            "sources": [],
            "error": False
        }
        
        result = await rag_service.chat_with_documents("What is this about?", "test-session")
        
        assert result["answer"] == "This is a fallback response."
        rag_service.llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_stats_success(self, rag_service):
        """Test successful document statistics retrieval."""
        rag_service.vector_store.get_collection_info.return_value = {
            "points_count": 100,
            "indexed_vectors_count": 95,
            "status": "green"
        }
        
        result = await rag_service.get_document_stats()
        
        assert result["total_documents"] == 100
        assert result["indexed_documents"] == 95
        assert result["collection_status"] == "green"
        assert result["vector_store_health"] is True

    @pytest.mark.asyncio
    async def test_get_document_stats_failure(self, rag_service):
        """Test document statistics retrieval when vector store fails."""
        rag_service.vector_store.get_collection_info.return_value = None
        
        result = await rag_service.get_document_stats()
        
        assert result["total_documents"] == 0
        assert result["vector_store_health"] is False

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, rag_service):
        """Test health check when all components are healthy."""
        # Setup mocks for healthy state
        rag_service.vector_store.health_check.return_value = True
        rag_service.embedding_client.check_model_availability.return_value = True
        rag_service.llm_client.check_model_availability.return_value = True
        
        result = await rag_service.health_check()
        
        assert result["overall_healthy"] is True
        assert result["vector_store"] is True
        assert result["embedding_client"] is True
        assert result["llm_client"] is True
        assert result["document_parser"] is True

    @pytest.mark.asyncio
    async def test_health_check_vector_store_unhealthy(self, rag_service):
        """Test health check when vector store is unhealthy."""
        rag_service.vector_store.health_check.return_value = False
        rag_service.embedding_client.check_model_availability.return_value = True
        rag_service.llm_client.check_model_availability.return_value = True
        
        result = await rag_service.health_check()
        
        assert result["overall_healthy"] is False
        assert result["vector_store"] is False

    @pytest.mark.asyncio
    async def test_health_check_clients_without_availability_check(self, rag_service):
        """Test health check when clients don't have availability check methods."""
        # Remove availability check methods (e.g., for API-based clients)
        delattr(rag_service.embedding_client, 'check_model_availability')
        delattr(rag_service.llm_client, 'check_model_availability')
        
        rag_service.vector_store.health_check.return_value = True
        
        result = await rag_service.health_check()
        
        assert result["overall_healthy"] is True
        assert result["embedding_client"] is True  # Assumed healthy for API clients
        assert result["llm_client"] is True  # Assumed healthy for API clients

    def test_create_chunks(self, rag_service):
        """Test document chunking functionality."""
        parsed_doc = {
            "text_content": [
                {"content": "Content 1", "page": 1},
                {"content": "Content 2", "page": 2},
                {"content": "   ", "page": 3},  # This should be skipped
                {"content": "Content 4", "page": 4}
            ],
            "metadata": {"num_pages": 4},
            "file_path": "/test/path/test.pdf",
            "format": "pdf"
        }
        
        chunks = rag_service._create_chunks(parsed_doc, "test.pdf")
        
        # Should create 3 chunks (skipping empty content)
        assert len(chunks) == 3
        
        # Check first chunk
        assert chunks[0]["content"] == "Content 1"
        assert chunks[0]["source"] == "test.pdf"
        assert chunks[0]["page"] == 1
        assert chunks[0]["chunk_index"] == 0
        
        # Check that chunk IDs are unique
        chunk_ids = [chunk["id"] for chunk in chunks]
        assert len(set(chunk_ids)) == len(chunk_ids)

    @pytest.mark.asyncio
    async def test_close(self, rag_service):
        """Test RAG service cleanup."""
        # Add close methods to mocked clients
        rag_service.embedding_client.close = AsyncMock()
        rag_service.llm_client.close = AsyncMock()
        
        await rag_service.close()
        
        rag_service.embedding_client.close.assert_called_once()
        rag_service.llm_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_close_methods(self, rag_service):
        """Test RAG service cleanup when clients don't have close methods."""
        # Ensure clients don't have close methods
        if hasattr(rag_service.embedding_client, 'close'):
            delattr(rag_service.embedding_client, 'close')
        if hasattr(rag_service.llm_client, 'close'):
            delattr(rag_service.llm_client, 'close')
        
        # Should not raise an exception
        await rag_service.close()


# Test the global service getter
@pytest.mark.asyncio
async def test_get_rag_service():
    """Test the global RAG service getter function."""
    from app.rag_service import get_rag_service
    
    # Clear any existing global service
    import app.rag_service
    app.rag_service.rag_service = None
    
    with patch('app.rag_service.RAGService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.initialize.return_value = True
        mock_service_class.return_value = mock_service
        
        # First call should create and initialize the service
        service1 = await get_rag_service()
        assert service1 == mock_service
        mock_service.initialize.assert_called_once()
        
        # Second call should return the same instance
        service2 = await get_rag_service()
        assert service2 == service1
        # Initialize should still only be called once
        mock_service.initialize.assert_called_once()