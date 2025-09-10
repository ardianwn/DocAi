import os
import logging
import uuid
import aiofiles
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Dict, Any, List
from pydantic import BaseModel

from .rag_service import get_rag_service, RAGService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocAI API",
    description="Document AI API for processing and querying documents with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS settings - Restrict to frontend domain only
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(',')
origins = [origin.strip() for origin in frontend_origins if origin.strip()]

logger.info(f"Configuring CORS for origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]] = []
    session_id: str = "default"
    error: bool = False

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging"""
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.on_event("startup")
async def startup_event():
    """Initialize RAG service on startup"""
    try:
        rag_service = await get_rag_service()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        raise

@app.get("/health")
async def health_check(rag_service: RAGService = Depends(get_rag_service)) -> Dict[str, Any]:
    """Comprehensive health check endpoint for container monitoring"""
    try:
        # Get RAG service health
        rag_health = await rag_service.health_check()
        
        # Get document statistics
        doc_stats = await rag_service.get_document_stats()
        
        health_status = {
            "status": "healthy" if rag_health.get("overall_healthy") else "unhealthy",
            "service": "docai-backend",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": rag_health,
            "document_stats": doc_stats,
            "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
            "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "ollama")
        }
        
        status_code = 200 if rag_health.get("overall_healthy") else 503
        
        if status_code == 503:
            raise HTTPException(status_code=503, detail=health_status)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "DocAI Backend API - RAG Document Processing",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "chat": "/chat",
            "documents": "/documents",
            "docs": "/docs"
        }
    }

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Upload and process document endpoint with full RAG pipeline"""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        logger.info(f"Uploading document: {file.filename}")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.doc', '.docx']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(allowed_extensions)}"
            )
        
        # Check file size
        max_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB default
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size // 1024 // 1024}MB"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Process document through RAG pipeline
        result = await rag_service.process_document(str(file_path), file.filename)
        
        if result.get("success"):
            logger.info(f"Document {file.filename} processed successfully")
            return {
                "message": f"Document {file.filename} uploaded and processed successfully",
                "filename": file.filename,
                "file_id": file_id,
                "size": file.size,
                "chunks_processed": result.get("chunks_processed", 0),
                "chunks_embedded": result.get("chunks_embedded", 0),
                "metadata": result.get("metadata", {})
            }
        else:
            # Clean up file if processing failed
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {str(e)}")
        # Clean up file if it was created
        if 'file_path' in locals():
            file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_documents(
    chat_request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Chat with documents endpoint using full RAG pipeline"""
    try:
        user_question = chat_request.question.strip()
        session_id = chat_request.session_id
        
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        if len(user_question) > 1000:
            raise HTTPException(status_code=400, detail="Question too long (max 1000 characters)")
        
        logger.info(f"Processing chat question for session {session_id}: {user_question[:100]}...")
        
        # Process question through RAG pipeline
        response = await rag_service.chat_with_documents(
            question=user_question,
            session_id=session_id,
            top_k=5
        )
        
        logger.info("Chat response generated successfully")
        return ChatResponse(
            question=response.get("question", user_question),
            answer=response.get("answer", ""),
            sources=response.get("sources", []),
            session_id=session_id,
            error=response.get("error", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")

@app.get("/documents")
async def get_document_stats(rag_service: RAGService = Depends(get_rag_service)):
    """Get document statistics and status"""
    try:
        stats = await rag_service.get_document_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document statistics")

@app.delete("/documents")
async def clear_all_documents(rag_service: RAGService = Depends(get_rag_service)):
    """Clear all documents from the vector store"""
    try:
        success = await rag_service.vector_store.clear_collection()
        
        if success:
            # Also clean up uploaded files
            for file_path in UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            return {
                "message": "All documents cleared successfully",
                "success": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear documents")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear documents")

@app.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get conversation history for a session"""
    try:
        history = rag_service.conversation_manager.get_history(session_id)
        return {
            "session_id": session_id,
            "history": history,
            "total_turns": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")

@app.delete("/sessions/{session_id}/history")
async def clear_conversation_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Clear conversation history for a session"""
    try:
        rag_service.conversation_manager.clear_history(session_id)
        return {
            "message": f"Conversation history cleared for session {session_id}",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation history")