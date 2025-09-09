"""
Ollama Embedding Module

This module handles text embedding generation using Ollama models for the DocAI system.
"""

import os
import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class OllamaEmbedding:
    """
    A class to handle text embedding generation using Ollama.
    
    This class provides methods to generate embeddings for text chunks
    using locally hosted Ollama models.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model_name: str = "nomic-embed-text",
                 timeout: int = 30):
        """
        Initialize the Ollama Embedding client.
        
        Args:
            base_url (str): Base URL for Ollama API
            model_name (str): Name of the embedding model to use
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"OllamaEmbedding initialized with model: {model_name}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def check_model_availability(self) -> bool:
        """
        Check if the specified embedding model is available in Ollama.
        
        Returns:
            bool: True if model is available, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            is_available = self.model_name in available_models
            logger.info(f"Model {self.model_name} availability: {is_available}")
            
            return is_available
            
        except Exception as e:
            logger.error(f"Error checking model availability: {str(e)}")
            return False
    
    async def pull_model(self) -> bool:
        """
        Pull the embedding model if it's not available locally.
        
        Returns:
            bool: True if model was pulled successfully, False otherwise
        """
        try:
            logger.info(f"Pulling model: {self.model_name}")
            
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name}
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error pulling model {self.model_name}: {str(e)}")
            return False
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        try:
            if not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            payload = {
                "model": self.model_name,
                "prompt": text.strip()
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get('embedding', [])
            
            if not embedding:
                logger.error("No embedding returned from Ollama")
                return None
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            batch_size (int): Number of texts to process in each batch
            
        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
            
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = []
                
                # Process batch concurrently
                tasks = [self.generate_embedding(text) for text in batch_texts]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in batch processing: {str(result)}")
                        batch_embeddings.append(None)
                    else:
                        batch_embeddings.append(result)
                
                embeddings.extend(batch_embeddings)
                
                # Small delay between batches to avoid overwhelming the server
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            logger.info(f"Generated {len([e for e in embeddings if e is not None])} embeddings successfully")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}")
            return [None] * len(texts)
    
    async def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks.
        
        Args:
            documents (List[Dict[str, Any]]): List of document chunks with text content
            
        Returns:
            List[Dict[str, Any]]: Document chunks with embeddings added
        """
        try:
            logger.info(f"Embedding {len(documents)} document chunks")
            
            # Extract text content from documents
            texts = []
            for doc in documents:
                text = doc.get('content', '') or doc.get('text', '')
                texts.append(text)
            
            # Generate embeddings
            embeddings = await self.generate_embeddings_batch(texts)
            
            # Add embeddings to documents
            embedded_docs = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                embedded_doc = doc.copy()
                embedded_doc['embedding'] = embedding
                embedded_doc['embedding_model'] = self.model_name
                embedded_doc['has_embedding'] = embedding is not None
                embedded_docs.append(embedded_doc)
            
            successful_embeddings = sum(1 for doc in embedded_docs if doc['has_embedding'])
            logger.info(f"Successfully embedded {successful_embeddings}/{len(documents)} documents")
            
            return embedded_docs
            
        except Exception as e:
            logger.error(f"Error embedding documents: {str(e)}")
            # Return documents without embeddings
            return [
                {**doc, 'embedding': None, 'embedding_model': self.model_name, 'has_embedding': False}
                for doc in documents
            ]
    
    async def get_embedding_dimension(self) -> Optional[int]:
        """
        Get the dimension of embeddings produced by the model.
        
        Returns:
            Optional[int]: Embedding dimension or None if failed
        """
        try:
            # Generate a test embedding to get dimension
            test_embedding = await self.generate_embedding("test")
            if test_embedding:
                return len(test_embedding)
            return None
            
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Utility functions for backwards compatibility
async def create_embeddings(texts: List[str], model_name: str = "nomic-embed-text") -> List[Optional[List[float]]]:
    """
    Utility function to create embeddings for a list of texts.
    
    Args:
        texts (List[str]): List of texts to embed
        model_name (str): Name of the embedding model
        
    Returns:
        List[Optional[List[float]]]: List of embedding vectors
    """
    async with OllamaEmbedding(model_name=model_name) as embedder:
        return await embedder.generate_embeddings_batch(texts)


async def create_embedding(text: str, model_name: str = "nomic-embed-text") -> Optional[List[float]]:
    """
    Utility function to create embedding for a single text.
    
    Args:
        text (str): Text to embed
        model_name (str): Name of the embedding model
        
    Returns:
        Optional[List[float]]: Embedding vector or None if failed
    """
    async with OllamaEmbedding(model_name=model_name) as embedder:
        return await embedder.generate_embedding(text)