"""
HuggingFace Client Module

This module handles interactions with HuggingFace models for embeddings and text generation.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import asyncio
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class HuggingFaceClient:
    """
    A client for HuggingFace models supporting both embeddings and text generation.
    """
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 task: str = "embedding",
                 device: str = "auto"):
        """
        Initialize the HuggingFace client.
        
        Args:
            model_name (str): Name of the HuggingFace model
            task (str): Task type ("embedding" or "text-generation")
            device (str): Device to use ("auto", "cpu", "cuda")
        """
        self.model_name = model_name
        self.task = task
        
        # Set device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        logger.info(f"HuggingFace client initialized with model: {model_name}, task: {task}, device: {self.device}")
    
    async def _load_model(self):
        """Load the model and tokenizer."""
        if self.model is not None:
            return
        
        try:
            loop = asyncio.get_event_loop()
            
            if self.task == "embedding":
                # Use SentenceTransformer for embeddings
                self.model = await loop.run_in_executor(
                    None,
                    lambda: SentenceTransformer(self.model_name, device=self.device)
                )
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
                
            elif self.task == "text-generation":
                # Load tokenizer and model for text generation
                self.tokenizer = await loop.run_in_executor(
                    None,
                    lambda: AutoTokenizer.from_pretrained(self.model_name)
                )
                
                self.model = await loop.run_in_executor(
                    None,
                    lambda: AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        device_map=self.device if self.device != "cpu" else None
                    )
                )
                
                # Create text generation pipeline
                self.pipeline = await loop.run_in_executor(
                    None,
                    lambda: pipeline(
                        "text-generation",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        device=0 if self.device == "cuda" else -1
                    )
                )
                
                logger.info(f"Loaded text generation model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model {self.model_name}: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text using HuggingFace model.
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        try:
            if not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            if self.task != "embedding":
                logger.error("Model not configured for embedding task")
                return None
            
            await self._load_model()
            
            # Generate embedding
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode([text.strip()])[0]
            )
            
            # Convert to list if numpy array
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            logger.debug(f"Generated HuggingFace embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating HuggingFace embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            batch_size (int): Number of texts to process in each batch
            
        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        try:
            logger.info(f"Generating HuggingFace embeddings for {len(texts)} texts")
            
            if self.task != "embedding":
                logger.error("Model not configured for embedding task")
                return [None] * len(texts)
            
            await self._load_model()
            
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Filter out empty texts and track indices
                valid_texts = []
                valid_indices = []
                
                for j, text in enumerate(batch_texts):
                    if text.strip():
                        valid_texts.append(text.strip())
                        valid_indices.append(j)
                
                if not valid_texts:
                    embeddings.extend([None] * len(batch_texts))
                    continue
                
                try:
                    # Generate embeddings for valid texts
                    loop = asyncio.get_event_loop()
                    batch_embeddings = await loop.run_in_executor(
                        None,
                        lambda: self.model.encode(valid_texts)
                    )
                    
                    # Map back to original batch order
                    batch_results = [None] * len(batch_texts)
                    for j, embedding in enumerate(batch_embeddings):
                        original_idx = valid_indices[j]
                        if isinstance(embedding, np.ndarray):
                            embedding = embedding.tolist()
                        batch_results[original_idx] = embedding
                    
                    embeddings.extend(batch_results)
                    
                except Exception as e:
                    logger.error(f"Error in batch embedding: {str(e)}")
                    embeddings.extend([None] * len(batch_texts))
            
            successful_count = len([e for e in embeddings if e is not None])
            logger.info(f"Generated {successful_count}/{len(texts)} HuggingFace embeddings successfully")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch HuggingFace embedding generation: {str(e)}")
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
            logger.info(f"Embedding {len(documents)} document chunks with HuggingFace")
            
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
            logger.info(f"Successfully embedded {successful_count}/{len(documents)} documents with HuggingFace")
            
            return embedded_docs
            
        except Exception as e:
            logger.error(f"Error embedding documents with HuggingFace: {str(e)}")
            return [
                {**doc, 'embedding': None, 'embedding_model': self.model_name, 'has_embedding': False}
                for doc in documents
            ]
    
    async def generate_response(self, 
                              question: str, 
                              context_documents: List[Dict[str, Any]] = None,
                              conversation_history: List[Dict[str, str]] = None,
                              max_length: int = 512) -> Dict[str, Any]:
        """
        Generate a text response using HuggingFace model.
        
        Args:
            question (str): User's question
            context_documents (List[Dict[str, Any]]): Retrieved documents for context
            conversation_history (List[Dict[str, str]]): Previous conversation
            max_length (int): Maximum length of generated text
            
        Returns:
            Dict[str, Any]: Response with answer and metadata
        """
        try:
            logger.info(f"Generating HuggingFace response for question: {question[:100]}...")
            
            if self.task != "text-generation":
                logger.error("Model not configured for text generation task")
                return {
                    "question": question,
                    "answer": "Model not configured for text generation",
                    "sources": [],
                    "error": True
                }
            
            await self._load_model()
            
            # Build prompt
            prompt_parts = []
            
            # Add system instruction
            prompt_parts.append("You are a helpful AI assistant that answers questions based on provided context.")
            
            # Add context if available
            if context_documents:
                context = self._format_context(context_documents)
                prompt_parts.append(f"Context:\n{context}")
            
            # Add conversation history
            if conversation_history:
                for turn in conversation_history[-3:]:  # Last 3 turns
                    prompt_parts.append(f"Human: {turn.get('question', '')}")
                    prompt_parts.append(f"Assistant: {turn.get('answer', '')}")
            
            # Add current question
            prompt_parts.append(f"Human: {question}")
            prompt_parts.append("Assistant:")
            
            prompt = "\n".join(prompt_parts)
            
            # Generate response
            loop = asyncio.get_event_loop()
            
            # Configure generation parameters
            generation_kwargs = {
                "max_length": len(prompt.split()) + max_length,
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "num_return_sequences": 1
            }
            
            outputs = await loop.run_in_executor(
                None,
                lambda: self.pipeline(prompt, **generation_kwargs)
            )
            
            # Extract generated text
            generated_text = outputs[0]['generated_text']
            
            # Extract only the assistant's response
            assistant_start = generated_text.rfind("Assistant:")
            if assistant_start != -1:
                answer = generated_text[assistant_start + len("Assistant:"):].strip()
            else:
                answer = generated_text[len(prompt):].strip()
            
            # Clean up the answer
            answer = answer.split("Human:")[0].strip()  # Stop at next human input
            
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
            
            logger.info("HuggingFace response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating HuggingFace response: {str(e)}")
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
            if self.task != "embedding":
                return None
            
            # Test embedding to get dimension
            test_embedding = await self.generate_embedding("test")
            if test_embedding:
                return len(test_embedding)
            return None
            
        except Exception as e:
            logger.error(f"Error getting HuggingFace embedding dimension: {str(e)}")
            return None


# Utility functions
async def create_huggingface_embedding(text: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[List[float]]:
    """
    Utility function to create a HuggingFace embedding for a single text.
    
    Args:
        text (str): Text to embed
        model_name (str): HuggingFace model name
        
    Returns:
        Optional[List[float]]: Embedding vector or None if failed
    """
    client = HuggingFaceClient(model_name=model_name, task="embedding")
    return await client.generate_embedding(text)


async def create_huggingface_embeddings(texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[Optional[List[float]]]:
    """
    Utility function to create HuggingFace embeddings for a list of texts.
    
    Args:
        texts (List[str]): List of texts to embed
        model_name (str): HuggingFace model name
        
    Returns:
        List[Optional[List[float]]]: List of embedding vectors
    """
    client = HuggingFaceClient(model_name=model_name, task="embedding")
    return await client.generate_embeddings_batch(texts)