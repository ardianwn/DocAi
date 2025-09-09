"""
OpenAI Client Module

This module handles interactions with OpenAI API for embeddings and chat.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
import asyncio

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    A client for OpenAI API supporting both embeddings and chat completions.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", timeout: int = 60):
        """
        Initialize the OpenAI client.
        
        Args:
            model_name (str): Name of the model to use
            timeout (int): Request timeout in seconds
        """
        self.model_name = model_name
        self.timeout = timeout
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        
        logger.info(f"OpenAI client initialized with model: {model_name}")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text using OpenAI API.
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        try:
            if not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            # Run in thread pool since OpenAI client is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.embeddings.create(
                    model=self.model_name,
                    input=text.strip()
                )
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated OpenAI embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            batch_size (int): Number of texts to process in each batch
            
        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        try:
            logger.info(f"Generating OpenAI embeddings for {len(texts)} texts")
            
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Filter out empty texts
                valid_texts = [text for text in batch_texts if text.strip()]
                
                if not valid_texts:
                    embeddings.extend([None] * len(batch_texts))
                    continue
                
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.embeddings.create(
                            model=self.model_name,
                            input=valid_texts
                        )
                    )
                    
                    batch_embeddings = [item.embedding for item in response.data]
                    
                    # Map back to original batch order
                    valid_idx = 0
                    for text in batch_texts:
                        if text.strip():
                            embeddings.append(batch_embeddings[valid_idx])
                            valid_idx += 1
                        else:
                            embeddings.append(None)
                            
                except Exception as e:
                    logger.error(f"Error in batch embedding: {str(e)}")
                    embeddings.extend([None] * len(batch_texts))
                
                # Small delay between batches
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            successful_count = len([e for e in embeddings if e is not None])
            logger.info(f"Generated {successful_count}/{len(texts)} OpenAI embeddings successfully")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch OpenAI embedding generation: {str(e)}")
            return [None] * len(texts)
    
    async def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks.
        
        Args:
            documents (List[Dict[str, Any]]): List of document chunks
            
        Returns:
            List[Dict[str, Any]]: Document chunks with embeddings added
        """
        try:
            logger.info(f"Embedding {len(documents)} document chunks with OpenAI")
            
            # Extract text content
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
            
            successful_count = sum(1 for doc in embedded_docs if doc['has_embedding'])
            logger.info(f"Successfully embedded {successful_count}/{len(documents)} documents with OpenAI")
            
            return embedded_docs
            
        except Exception as e:
            logger.error(f"Error embedding documents with OpenAI: {str(e)}")
            return [
                {**doc, 'embedding': None, 'embedding_model': self.model_name, 'has_embedding': False}
                for doc in documents
            ]
    
    async def generate_response(self, 
                              question: str, 
                              context_documents: List[Dict[str, Any]] = None,
                              conversation_history: List[Dict[str, str]] = None,
                              max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a chat response using OpenAI API.
        
        Args:
            question (str): User's question
            context_documents (List[Dict[str, Any]]): Retrieved documents for context
            conversation_history (List[Dict[str, str]]): Previous conversation
            max_tokens (int): Maximum tokens in response
            
        Returns:
            Dict[str, Any]: Response with answer and metadata
        """
        try:
            logger.info(f"Generating OpenAI response for question: {question[:100]}...")
            
            # Build messages for OpenAI chat completion
            messages = []
            
            # System message
            system_content = """You are a helpful AI assistant that answers questions based on the provided document context. 
Follow these guidelines:
1. Answer questions using only the information from the provided context
2. If the context doesn't contain enough information to answer the question, say so
3. Be concise but comprehensive in your responses
4. Cite specific parts of the context when relevant
5. If asked about something not in the context, politely explain that the information is not available in the provided documents"""
            
            messages.append({"role": "system", "content": system_content})
            
            # Add conversation history
            if conversation_history:
                for turn in conversation_history[-5:]:  # Last 5 turns
                    messages.append({"role": "user", "content": turn.get('question', '')})
                    messages.append({"role": "assistant", "content": turn.get('answer', '')})
            
            # Add context if available
            if context_documents:
                context = self._format_context(context_documents)
                context_message = f"Here is the relevant context from the documents:\n\n{context}"
                messages.append({"role": "system", "content": context_message})
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
            )
            
            answer = response.choices[0].message.content
            
            # Extract sources from context documents
            sources = []
            if context_documents:
                for doc in context_documents:
                    source_info = {
                        'source': doc.get('source', ''),
                        'page': doc.get('page'),
                        'score': doc.get('score', 0.0),
                        'content_preview': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', '')
                    }
                    sources.append(source_info)
            
            result = {
                "question": question,
                "answer": answer,
                "sources": sources,
                "model": self.model_name,
                "context_used": len(context_documents) if context_documents else 0,
                "error": False
            }
            
            logger.info("OpenAI response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return {
                "question": question,
                "answer": f"I'm sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": True
            }
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context for the model.
        
        Args:
            documents (List[Dict[str, Any]]): Retrieved documents
            
        Returns:
            str: Formatted context string
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '').strip()
            source = doc.get('source', 'Unknown source')
            page = doc.get('page')
            
            context_part = f"Document {i}:\nSource: {source}"
            if page:
                context_part += f" (Page {page})"
            context_part += f"\nContent: {content}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    async def get_embedding_dimension(self) -> Optional[int]:
        """
        Get the dimension of embeddings produced by the model.
        
        Returns:
            Optional[int]: Embedding dimension or None if failed
        """
        try:
            # Test embedding to get dimension
            test_embedding = await self.generate_embedding("test")
            if test_embedding:
                return len(test_embedding)
            return None
            
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding dimension: {str(e)}")
            return None


# Utility functions
async def create_openai_embedding(text: str, model_name: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Utility function to create an OpenAI embedding for a single text.
    
    Args:
        text (str): Text to embed
        model_name (str): OpenAI embedding model name
        
    Returns:
        Optional[List[float]]: Embedding vector or None if failed
    """
    client = OpenAIClient(model_name=model_name)
    return await client.generate_embedding(text)


async def create_openai_embeddings(texts: List[str], model_name: str = "text-embedding-3-small") -> List[Optional[List[float]]]:
    """
    Utility function to create OpenAI embeddings for a list of texts.
    
    Args:
        texts (List[str]): List of texts to embed
        model_name (str): OpenAI embedding model name
        
    Returns:
        List[Optional[List[float]]]: List of embedding vectors
    """
    client = OpenAIClient(model_name=model_name)
    return await client.generate_embeddings_batch(texts)