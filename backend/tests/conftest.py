"""
Test configuration and fixtures for the DocAI backend tests.
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Set test environment variables
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["QDRANT_HOST"] = "mock"
os.environ["LOG_LEVEL"] = "WARNING"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock = AsyncMock()
    mock.generate_response.return_value = {
        "question": "test question",
        "answer": "test answer",
        "sources": [],
        "error": False
    }
    mock.check_model_availability.return_value = True
    return mock

@pytest.fixture
def mock_embedding_client():
    """Mock embedding client for testing."""
    mock = AsyncMock()
    mock.generate_embedding.return_value = [0.1] * 768
    mock.generate_embeddings_batch.return_value = [[0.1] * 768]
    mock.embed_documents.return_value = [
        {
            "content": "test content",
            "embedding": [0.1] * 768,
            "has_embedding": True,
            "embedding_model": "test-model"
        }
    ]
    mock.check_model_availability.return_value = True
    mock.get_embedding_dimension.return_value = 768
    return mock

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock = AsyncMock()
    mock.health_check.return_value = True
    mock.create_collection.return_value = True
    mock.upsert_documents.return_value = True
    mock.search_similar.return_value = [
        {
            "id": "test-doc-1",
            "score": 0.9,
            "content": "test content",
            "source": "test.pdf",
            "page": 1
        }
    ]
    mock.get_collection_info.return_value = {
        "points_count": 10,
        "indexed_vectors_count": 10,
        "status": "green"
    }
    return mock

@pytest.fixture
def mock_document_parser():
    """Mock document parser for testing."""
    mock = AsyncMock()
    mock.parse_document.return_value = {
        "text_content": [
            {"content": "Test content 1", "page": 1},
            {"content": "Test content 2", "page": 2}
        ],
        "metadata": {"num_pages": 2, "title": "Test Document"},
        "file_path": "/test/path/test.pdf",
        "format": "pdf"
    }
    return mock

@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF file for testing."""
    # In a real test environment, you would put a sample PDF here
    return Path(__file__).parent / "fixtures" / "sample.pdf"

@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return "This is a sample document content for testing purposes."

@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [[0.1, 0.2, 0.3] * 256]  # 768-dimensional vector

@pytest.fixture
def sample_chat_history():
    """Sample chat history for testing."""
    return [
        {"question": "What is the document about?", "answer": "This is a test document."},
        {"question": "Can you provide more details?", "answer": "It contains sample content."}
    ]