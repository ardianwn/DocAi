"""
Qdrant Client Module

This module handles vector database operations using Qdrant for the DocAI system.
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    VectorParams, 
    Distance, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue,
    SearchRequest
)
import asyncio

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    A class to handle vector database operations using Qdrant.
    
    This class provides methods to store, search, and manage document embeddings
    in a Qdrant vector database.
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6333,
                 collection_name: str = "documents",
                 vector_size: int = 768):
        """
        Initialize the Qdrant client.
        
        Args:
            host (str): Qdrant server host
            port (int): Qdrant server port
            collection_name (str): Name of the collection to use
            vector_size (int): Dimension of the embedding vectors
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        try:
            self.client = QdrantClient(host=host, port=port)
            logger.info(f"Qdrant client initialized: {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Qdrant server is healthy and accessible.
        
        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # Use asyncio to run the sync operation
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self.client.get_cluster_info)
            logger.info("Qdrant health check passed")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return False
    
    async def create_collection(self, overwrite: bool = False) -> bool:
        """
        Create a collection for storing document embeddings.
        
        Args:
            overwrite (bool): Whether to overwrite existing collection
            
        Returns:
            bool: True if collection was created/exists, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Check if collection already exists
            collections = await loop.run_in_executor(None, self.client.get_collections)
            existing_collections = [col.name for col in collections.collections]
            
            if self.collection_name in existing_collections:
                if overwrite:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    await loop.run_in_executor(None, self.client.delete_collection, self.collection_name)
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return True
            
            # Create new collection
            logger.info(f"Creating collection: {self.collection_name}")
            await loop.run_in_executor(
                None,
                self.client.create_collection,
                self.collection_name,
                VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
            
            logger.info(f"Collection {self.collection_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False
    
    async def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Insert or update documents in the vector store.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents with embeddings
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            if not documents:
                logger.warning("No documents provided for upsert")
                return True
            
            # Prepare points for Qdrant
            points = []
            for doc in documents:
                if not doc.get('embedding') or not doc.get('has_embedding', False):
                    logger.warning(f"Skipping document without embedding: {doc.get('id', 'unknown')}")
                    continue
                
                # Generate unique ID if not provided
                doc_id = doc.get('id') or str(uuid.uuid4())
                
                # Prepare payload (metadata)
                payload = {
                    'content': doc.get('content', ''),
                    'source': doc.get('source', ''),
                    'page': doc.get('page'),
                    'chunk_index': doc.get('chunk_index'),
                    'file_path': doc.get('file_path', ''),
                    'format': doc.get('format', ''),
                    'created_at': doc.get('created_at'),
                    'embedding_model': doc.get('embedding_model', '')
                }
                
                # Remove None values
                payload = {k: v for k, v in payload.items() if v is not None}
                
                point = PointStruct(
                    id=doc_id,
                    vector=doc['embedding'],
                    payload=payload
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid documents with embeddings to upsert")
                return True
            
            # Upsert points to Qdrant
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.upsert,
                self.collection_name,
                points
            )
            
            logger.info(f"Successfully upserted {len(points)} documents to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting documents: {str(e)}")
            return False
    
    async def search_similar(self, 
                           query_vector: List[float], 
                           limit: int = 5,
                           score_threshold: float = 0.0,
                           filter_conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on vector similarity.
        
        Args:
            query_vector (List[float]): Query embedding vector
            limit (int): Maximum number of results to return
            score_threshold (float): Minimum similarity score threshold
            filter_conditions (Optional[Dict[str, Any]]): Additional filter conditions
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with scores
        """
        try:
            # Prepare filter if provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Perform search
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                self.client.search,
                self.collection_name,
                query_vector,
                query_filter,
                limit,
                True  # with_payload
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                if scored_point.score >= score_threshold:
                    result = {
                        'id': scored_point.id,
                        'score': scored_point.score,
                        'content': scored_point.payload.get('content', ''),
                        'source': scored_point.payload.get('source', ''),
                        'page': scored_point.payload.get('page'),
                        'chunk_index': scored_point.payload.get('chunk_index'),
                        'file_path': scored_point.payload.get('file_path', ''),
                        'format': scored_point.payload.get('format', ''),
                        'metadata': scored_point.payload
                    }
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar documents (threshold: {score_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            return []
    
    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the collection.
        
        Returns:
            Optional[Dict[str, Any]]: Collection information or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
            collection_info = await loop.run_in_executor(
                None,
                self.client.get_collection,
                self.collection_name
            )
            
            info = {
                'name': collection_info.config.name,
                'vectors_count': collection_info.vectors_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'points_count': collection_info.points_count,
                'status': collection_info.status.value if collection_info.status else 'unknown',
                'optimizer_status': collection_info.optimizer_status.status.value if collection_info.optimizer_status else 'unknown'
            }
            
            logger.info(f"Collection info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents by their IDs.
        
        Args:
            document_ids (List[str]): List of document IDs to delete
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            if not document_ids:
                logger.warning("No document IDs provided for deletion")
                return True
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.delete,
                self.collection_name,
                document_ids
            )
            
            logger.info(f"Successfully deleted {len(document_ids)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    async def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Delete the collection and recreate it
            await loop.run_in_executor(None, self.client.delete_collection, self.collection_name)
            
            # Recreate the collection
            success = await self.create_collection()
            
            if success:
                logger.info(f"Collection {self.collection_name} cleared successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False


# Utility functions for backwards compatibility
async def create_vector_store(host: str = "localhost", 
                            port: int = 6333, 
                            collection_name: str = "documents") -> QdrantVectorStore:
    """
    Utility function to create and initialize a vector store.
    
    Args:
        host (str): Qdrant server host
        port (int): Qdrant server port
        collection_name (str): Name of the collection
        
    Returns:
        QdrantVectorStore: Initialized vector store instance
    """
    store = QdrantVectorStore(host=host, port=port, collection_name=collection_name)
    await store.create_collection()
    return store


async def search_documents(query_vector: List[float], 
                         limit: int = 5,
                         host: str = "localhost",
                         port: int = 6333,
                         collection_name: str = "documents") -> List[Dict[str, Any]]:
    """
    Utility function to search for similar documents.
    
    Args:
        query_vector (List[float]): Query embedding vector
        limit (int): Maximum number of results
        host (str): Qdrant server host
        port (int): Qdrant server port
        collection_name (str): Collection name
        
    Returns:
        List[Dict[str, Any]]: List of similar documents
    """
    store = QdrantVectorStore(host=host, port=port, collection_name=collection_name)
    return await store.search_similar(query_vector, limit=limit)