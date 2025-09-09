"""
RAG Service Module

This module integrates all RAG components: document parsing, embedding, vector storage, and chat.
"""

import os
import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .pdf_parser import PDFParser
from .embedding_ollama import OllamaEmbedding
from .qdrant_client import QdrantVectorStore
from .chat_llama import LlamaChat, ConversationManager
from .openai_client import OpenAIClient
from .huggingface_client import HuggingFaceClient

logger = logging.getLogger(__name__)


class RAGService:
    """
    Main RAG service that orchestrates document processing, embedding, and chat.
    """
    
    def __init__(self):
        """Initialize the RAG service with configured providers."""
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
        
        # Initialize components
        self.document_parser = PDFParser()
        self.conversation_manager = ConversationManager()
        
        # Initialize providers based on configuration
        self._init_embedding_client()
        self._init_llm_client()
        self._init_vector_store()
        
        logger.info(f"RAG Service initialized with LLM: {self.llm_provider}, Embedding: {self.embedding_provider}")
    
    def _init_embedding_client(self):
        """Initialize embedding client based on provider."""
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        
        if self.embedding_provider == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.embedding_client = OllamaEmbedding(
                base_url=ollama_url,
                model_name=embedding_model
            )
        elif self.embedding_provider == "openai":
            self.embedding_client = OpenAIClient(model_name=embedding_model)
        elif self.embedding_provider == "huggingface":
            self.embedding_client = HuggingFaceClient(
                model_name=embedding_model,
                task="embedding"
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    def _init_llm_client(self):
        """Initialize LLM client based on provider."""
        llm_model = os.getenv("LLM_MODEL", "llama2")
        
        if self.llm_provider == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.llm_client = LlamaChat(
                base_url=ollama_url,
                model_name=llm_model
            )
        elif self.llm_provider == "openai":
            self.llm_client = OpenAIClient(model_name=llm_model)
        elif self.llm_provider == "huggingface":
            self.llm_client = HuggingFaceClient(
                model_name=llm_model,
                task="text-generation"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _init_vector_store(self):
        """Initialize vector store."""
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        collection_name = os.getenv("COLLECTION_NAME", "documents")
        vector_size = int(os.getenv("VECTOR_SIZE", "768"))
        
        self.vector_store = QdrantVectorStore(
            host=qdrant_host,
            port=qdrant_port,
            collection_name=collection_name,
            vector_size=vector_size
        )
    
    async def initialize(self) -> bool:
        """
        Initialize all components and check health.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize vector store collection
            await self.vector_store.create_collection()
            
            # Check vector store health
            vector_health = await self.vector_store.health_check()
            if not vector_health:
                logger.error("Vector store health check failed")
                return False
            
            # Check embedding client availability
            if hasattr(self.embedding_client, 'check_model_availability'):
                embedding_health = await self.embedding_client.check_model_availability()
                if not embedding_health:
                    logger.warning("Embedding model not available, attempting to pull...")
                    if hasattr(self.embedding_client, 'pull_model'):
                        await self.embedding_client.pull_model()
            
            # Check LLM client availability
            if hasattr(self.llm_client, 'check_model_availability'):
                llm_health = await self.llm_client.check_model_availability()
                if not llm_health:
                    logger.warning("LLM model not available, attempting to pull...")
                    if hasattr(self.llm_client, 'pull_model'):
                        await self.llm_client.pull_model()
            
            logger.info("RAG Service initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}")
            return False
    
    async def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Process a document: parse, chunk, embed, and store.
        
        Args:
            file_path (str): Path to the document file
            filename (str): Original filename
            
        Returns:
            Dict[str, Any]: Processing results
        """
        try:
            logger.info(f"Processing document: {filename}")
            
            # Parse document
            parsed_doc = await self.document_parser.parse_document(file_path)
            
            if not parsed_doc or not parsed_doc.get('text_content'):
                return {
                    "success": False,
                    "error": "Failed to extract text from document"
                }
            
            # Create document chunks
            chunks = self._create_chunks(parsed_doc, filename)
            
            if not chunks:
                return {
                    "success": False,
                    "error": "No content chunks created from document"
                }
            
            # Generate embeddings
            embedded_chunks = await self.embedding_client.embed_documents(chunks)
            
            # Filter successful embeddings
            valid_chunks = [chunk for chunk in embedded_chunks if chunk.get('has_embedding')]
            
            if not valid_chunks:
                return {
                    "success": False,
                    "error": "Failed to generate embeddings for document"
                }
            
            # Store in vector database
            storage_success = await self.vector_store.upsert_documents(valid_chunks)
            
            if not storage_success:
                return {
                    "success": False,
                    "error": "Failed to store document in vector database"
                }
            
            result = {
                "success": True,
                "filename": filename,
                "chunks_processed": len(chunks),
                "chunks_embedded": len(valid_chunks),
                "metadata": parsed_doc.get('metadata', {})
            }
            
            logger.info(f"Successfully processed document {filename}: {len(valid_chunks)} chunks stored")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def _create_chunks(self, parsed_doc: Dict[str, Any], filename: str) -> List[Dict[str, Any]]:
        """
        Create chunks from parsed document content.
        
        Args:
            parsed_doc (Dict[str, Any]): Parsed document data
            filename (str): Original filename
            
        Returns:
            List[Dict[str, Any]]: Document chunks
        """
        chunks = []
        text_content = parsed_doc.get('text_content', [])
        
        for i, content_item in enumerate(text_content):
            content = content_item.get('content', '').strip()
            
            if len(content) < 10:  # Skip very short content
                continue
            
            chunk = {
                'id': str(uuid.uuid4()),
                'content': content,
                'source': filename,
                'file_path': parsed_doc.get('file_path', ''),
                'format': parsed_doc.get('format', ''),
                'chunk_index': i,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    **parsed_doc.get('metadata', {}),
                    **content_item
                }
            }
            
            # Add page number if available
            if 'page' in content_item:
                chunk['page'] = content_item['page']
            
            chunks.append(chunk)
        
        return chunks
    
    async def chat_with_documents(self, 
                                question: str, 
                                session_id: str = "default",
                                top_k: int = 5) -> Dict[str, Any]:
        """
        Chat with documents using RAG.
        
        Args:
            question (str): User's question
            session_id (str): Session identifier for conversation history
            top_k (int): Number of relevant documents to retrieve
            
        Returns:
            Dict[str, Any]: Chat response with answer and sources
        """
        try:
            logger.info(f"Processing chat question: {question[:100]}...")
            
            # Generate embedding for the question
            question_embedding = await self.embedding_client.generate_embedding(question)
            
            if not question_embedding:
                return {
                    "question": question,
                    "answer": "I'm sorry, I couldn't process your question at the moment.",
                    "sources": [],
                    "error": True
                }
            
            # Retrieve relevant documents
            relevant_docs = await self.vector_store.search_similar(
                query_vector=question_embedding,
                limit=top_k,
                score_threshold=0.1
            )
            
            # Get conversation history
            conversation_history = self.conversation_manager.get_history(session_id)
            
            # Generate response using LLM
            if hasattr(self.llm_client, 'chat_with_documents'):
                response = await self.llm_client.chat_with_documents(
                    question=question,
                    retrieved_documents=relevant_docs,
                    conversation_history=conversation_history
                )
            else:
                # Fallback for OpenAI/HuggingFace clients
                response = await self.llm_client.generate_response(
                    question=question,
                    context_documents=relevant_docs,
                    conversation_history=conversation_history
                )
            
            # Add to conversation history
            if not response.get('error'):
                self.conversation_manager.add_turn(
                    session_id=session_id,
                    question=question,
                    answer=response.get('answer', '')
                )
            
            logger.info("Chat response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                "question": question,
                "answer": f"I'm sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": True
            }
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored documents.
        
        Returns:
            Dict[str, Any]: Document statistics
        """
        try:
            collection_info = await self.vector_store.get_collection_info()
            
            if collection_info:
                return {
                    "total_documents": collection_info.get('points_count', 0),
                    "indexed_documents": collection_info.get('indexed_vectors_count', 0),
                    "collection_status": collection_info.get('status', 'unknown'),
                    "vector_store_health": True
                }
            else:
                return {
                    "total_documents": 0,
                    "indexed_documents": 0,
                    "collection_status": "unavailable",
                    "vector_store_health": False
                }
                
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {
                "total_documents": 0,
                "indexed_documents": 0,
                "collection_status": "error",
                "vector_store_health": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check of all RAG components.
        
        Returns:
            Dict[str, Any]: Health status of all components
        """
        health_status = {
            "rag_service": True,
            "vector_store": False,
            "embedding_client": False,
            "llm_client": False,
            "document_parser": True
        }
        
        try:
            # Check vector store
            health_status["vector_store"] = await self.vector_store.health_check()
            
            # Check embedding client
            if hasattr(self.embedding_client, 'check_model_availability'):
                health_status["embedding_client"] = await self.embedding_client.check_model_availability()
            else:
                health_status["embedding_client"] = True  # Assume healthy for API-based clients
            
            # Check LLM client
            if hasattr(self.llm_client, 'check_model_availability'):
                health_status["llm_client"] = await self.llm_client.check_model_availability()
            else:
                health_status["llm_client"] = True  # Assume healthy for API-based clients
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            health_status["error"] = str(e)
        
        health_status["overall_healthy"] = all([
            health_status["vector_store"],
            health_status["embedding_client"],
            health_status["llm_client"],
            health_status["document_parser"]
        ])
        
        return health_status
    
    async def close(self):
        """Close all client connections."""
        try:
            if hasattr(self.embedding_client, 'close'):
                await self.embedding_client.close()
            
            if hasattr(self.llm_client, 'close'):
                await self.llm_client.close()
                
            logger.info("RAG Service closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing RAG service: {str(e)}")


# Global RAG service instance
rag_service = None

async def get_rag_service() -> RAGService:
    """
    Get or create the global RAG service instance.
    
    Returns:
        RAGService: The RAG service instance
    """
    global rag_service
    
    if rag_service is None:
        rag_service = RAGService()
        await rag_service.initialize()
    
    return rag_service