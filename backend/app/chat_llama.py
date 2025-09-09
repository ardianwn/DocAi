"""
Chat Llama Module

This module handles chat interactions using Llama models for the DocAI system.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
import asyncio

logger = logging.getLogger(__name__)


class LlamaChat:
    """
    A class to handle chat interactions using Llama models via Ollama.
    
    This class provides methods for generating responses based on retrieved
    document contexts and maintaining conversation history.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model_name: str = "llama2",
                 timeout: int = 60,
                 max_tokens: int = 2048):
        """
        Initialize the Llama Chat client.
        
        Args:
            base_url (str): Base URL for Ollama API
            model_name (str): Name of the Llama model to use
            timeout (int): Request timeout in seconds
            max_tokens (int): Maximum tokens in response
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # System prompt for RAG
        self.system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 
Follow these guidelines:
1. Answer questions using only the information from the provided context
2. If the context doesn't contain enough information to answer the question, say so
3. Be concise but comprehensive in your responses
4. Cite specific parts of the context when relevant
5. If asked about something not in the context, politely explain that the information is not available in the provided documents"""
        
        logger.info(f"LlamaChat initialized with model: {model_name}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def check_model_availability(self) -> bool:
        """
        Check if the specified model is available in Ollama.
        
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
        Pull the model if it's not available locally.
        
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
    
    def _build_prompt(self, question: str, context: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Build the complete prompt for the model.
        
        Args:
            question (str): User's question
            context (str): Retrieved document context
            conversation_history (List[Dict[str, str]]): Previous conversation turns
            
        Returns:
            str: Complete prompt
        """
        prompt_parts = [self.system_prompt]
        
        # Add conversation history if provided
        if conversation_history:
            prompt_parts.append("\n--- Previous Conversation ---")
            for turn in conversation_history[-5:]:  # Last 5 turns
                prompt_parts.append(f"Human: {turn.get('question', '')}")
                prompt_parts.append(f"Assistant: {turn.get('answer', '')}")
        
        # Add current context and question
        prompt_parts.extend([
            "\n--- Document Context ---",
            context,
            "\n--- Question ---",
            f"Human: {question}",
            "Assistant:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def generate_response(self, 
                              question: str, 
                              context_documents: List[Dict[str, Any]] = None,
                              conversation_history: List[Dict[str, str]] = None,
                              stream: bool = False) -> Dict[str, Any]:
        """
        Generate a response to a question using the provided context.
        
        Args:
            question (str): User's question
            context_documents (List[Dict[str, Any]]): Retrieved documents for context
            conversation_history (List[Dict[str, str]]): Previous conversation
            stream (bool): Whether to stream the response
            
        Returns:
            Dict[str, Any]: Response with answer and metadata
        """
        try:
            logger.info(f"Generating response for question: {question[:100]}...")
            
            # Format context
            context = self._format_context(context_documents or [])
            
            # Build prompt
            prompt = self._build_prompt(question, context, conversation_history)
            
            # Prepare request
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop": ["Human:", "User:"]
                }
            }
            
            if stream:
                return await self._generate_streaming_response(payload, question, context_documents)
            else:
                return await self._generate_complete_response(payload, question, context_documents)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "question": question,
                "answer": f"I'm sorry, I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "error": True
            }
    
    async def _generate_complete_response(self, payload: Dict[str, Any], question: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a complete (non-streaming) response."""
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        answer = result.get('response', '').strip()
        
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
        
        response_data = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "model": self.model_name,
            "context_used": len(context_documents) if context_documents else 0,
            "error": False
        }
        
        logger.info("Response generated successfully")
        return response_data
    
    async def _generate_streaming_response(self, payload: Dict[str, Any], question: str, context_documents: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a streaming response."""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                accumulated_response = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk_data = json.loads(line)
                            if chunk_data.get('response'):
                                accumulated_response += chunk_data['response']
                                
                                yield {
                                    "type": "chunk",
                                    "content": chunk_data['response'],
                                    "accumulated": accumulated_response
                                }
                            
                            if chunk_data.get('done', False):
                                # Final response with sources
                                sources = []
                                if context_documents:
                                    for doc in context_documents:
                                        source_info = {
                                            'source': doc.get('source', ''),
                                            'page': doc.get('page'),
                                            'score': doc.get('score', 0.0)
                                        }
                                        sources.append(source_info)
                                
                                yield {
                                    "type": "complete",
                                    "question": question,
                                    "answer": accumulated_response,
                                    "sources": sources,
                                    "model": self.model_name,
                                    "context_used": len(context_documents) if context_documents else 0,
                                    "error": False
                                }
                                return
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield {
                "type": "error",
                "question": question,
                "answer": f"I'm sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": True
            }
    
    async def chat_with_documents(self, 
                                question: str, 
                                retrieved_documents: List[Dict[str, Any]],
                                conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Main method for chatting with documents.
        
        Args:
            question (str): User's question
            retrieved_documents (List[Dict[str, Any]]): Documents retrieved from vector search
            conversation_history (List[Dict[str, str]]): Previous conversation turns
            
        Returns:
            Dict[str, Any]: Complete response with answer and sources
        """
        return await self.generate_response(
            question=question,
            context_documents=retrieved_documents,
            conversation_history=conversation_history,
            stream=False
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class ConversationManager:
    """
    A class to manage conversation history and context.
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialize the conversation manager.
        
        Args:
            max_history (int): Maximum number of conversation turns to keep
        """
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def add_turn(self, session_id: str, question: str, answer: str):
        """
        Add a conversation turn to the history.
        
        Args:
            session_id (str): Unique session identifier
            question (str): User's question
            answer (str): Assistant's answer
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "question": question,
            "answer": answer,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only the most recent turns
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            List[Dict[str, str]]: Conversation history
        """
        return self.conversations.get(session_id, [])
    
    def clear_history(self, session_id: str):
        """
        Clear conversation history for a session.
        
        Args:
            session_id (str): Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]


# Utility functions for backwards compatibility
async def generate_chat_response(question: str, 
                               context_documents: List[Dict[str, Any]],
                               model_name: str = "llama2") -> Dict[str, Any]:
    """
    Utility function to generate a chat response.
    
    Args:
        question (str): User's question
        context_documents (List[Dict[str, Any]]): Retrieved documents
        model_name (str): Name of the model to use
        
    Returns:
        Dict[str, Any]: Response with answer and sources
    """
    async with LlamaChat(model_name=model_name) as chat:
        return await chat.chat_with_documents(question, context_documents)