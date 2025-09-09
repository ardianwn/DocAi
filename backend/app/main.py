import os
import logging
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Dict, Any

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
    description="Document AI API for processing and querying documents",
    version="1.0.0"
)

# CORS settings - Restrict to frontend domain only
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(',')
origins = [origin.strip() for origin in frontend_origins if origin.strip()]

logger.info(f"Configuring CORS for origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging"""
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for container monitoring"""
    try:
        return {
            "status": "healthy",
            "service": "docai-backend",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DocAI Backend API", "status": "running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document endpoint"""
    try:
        logger.info(f"Uploading document: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, TXT, DOC, or DOCX files."
            )
        
        # TODO: Implement document processing logic
        logger.info(f"Document {file.filename} uploaded successfully")
        
        return {
            "message": f"Document {file.filename} uploaded successfully",
            "filename": file.filename,
            "size": file.size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/chat")
async def chat_with_documents(question: dict):
    """Chat with documents endpoint"""
    try:
        user_question = question.get("question", "").strip()
        
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        logger.info(f"Processing chat question: {user_question[:100]}...")
        
        # TODO: Implement chat logic with document retrieval
        
        response = {
            "question": user_question,
            "answer": "This is a placeholder response. Document processing not yet implemented.",
            "sources": []
        }
        
        logger.info("Chat response generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")