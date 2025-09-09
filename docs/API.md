# DocAI API Documentation

## Overview

The DocAI API provides endpoints for document upload, processing, and AI-powered chat functionality. All endpoints return JSON responses and support standard HTTP status codes.

**Base URL**: `http://localhost:8000`

## Authentication

Currently, no authentication is required for the API endpoints. In production environments, implement appropriate authentication mechanisms.

## Content Types

- **Request**: `application/json` (except file uploads)
- **Response**: `application/json`
- **File Uploads**: `multipart/form-data`

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Endpoints

### Health Check

**GET** `/health`

Returns the health status of all system components.

**Response**:
```json
{
  "status": "healthy",
  "service": "docai-backend",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "components": {
    "rag_service": true,
    "vector_store": true,
    "embedding_client": true,
    "llm_client": true,
    "document_parser": true,
    "overall_healthy": true
  },
  "document_stats": {
    "total_documents": 42,
    "indexed_documents": 40,
    "collection_status": "green",
    "vector_store_health": true
  },
  "llm_provider": "ollama",
  "embedding_provider": "ollama"
}
```

### Root Information

**GET** `/`

Returns basic API information and available endpoints.

**Response**:
```json
{
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
```

### Document Upload

**POST** `/upload`

Upload and process a document for later querying.

**Request**:
- Content-Type: `multipart/form-data`
- File parameter: `file`

**Supported File Types**:
- PDF (`.pdf`)
- Text (`.txt`)
- Word Document (`.doc`, `.docx`)

**File Size Limit**: 50MB (configurable)

**Example**:
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

**Response**:
```json
{
  "message": "Document document.pdf uploaded and processed successfully",
  "filename": "document.pdf",
  "file_id": "uuid-string",
  "size": 1024000,
  "chunks_processed": 25,
  "chunks_embedded": 25,
  "metadata": {
    "num_pages": 10,
    "title": "Sample Document",
    "format": "pdf"
  }
}
```

**Error Response**:
```json
{
  "detail": "Unsupported file type: .xyz. Supported: .pdf, .txt, .doc, .docx"
}
```

### Chat with Documents

**POST** `/chat`

Send a question and get an AI-generated answer based on uploaded documents.

**Request Body**:
```json
{
  "question": "What is the main topic of the document?",
  "session_id": "user-session-123"
}
```

**Parameters**:
- `question` (string, required): The user's question
- `session_id` (string, optional): Session identifier for conversation history

**Example**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic?",
    "session_id": "my-session"
  }'
```

**Response**:
```json
{
  "question": "What is the main topic of the document?",
  "answer": "The main topic of the document is artificial intelligence and its applications in modern business processes.",
  "sources": [
    {
      "source": "document.pdf",
      "page": 1,
      "score": 0.95,
      "content_preview": "Artificial intelligence (AI) has revolutionized..."
    },
    {
      "source": "document.pdf", 
      "page": 3,
      "score": 0.87,
      "content_preview": "Business processes have been transformed..."
    }
  ],
  "session_id": "user-session-123",
  "error": false
}
```

**Error Response**:
```json
{
  "question": "What is the main topic?",
  "answer": "I'm sorry, I encountered an error: No documents found",
  "sources": [],
  "session_id": "user-session-123", 
  "error": true
}
```

### Document Statistics

**GET** `/documents`

Get statistics about uploaded and processed documents.

**Response**:
```json
{
  "total_documents": 42,
  "indexed_documents": 40,
  "collection_status": "green",
  "vector_store_health": true
}
```

### Clear All Documents

**DELETE** `/documents`

Remove all documents from the vector store and file system.

**Response**:
```json
{
  "message": "All documents cleared successfully",
  "success": true
}
```

### Conversation History

**GET** `/sessions/{session_id}/history`

Retrieve conversation history for a specific session.

**Parameters**:
- `session_id` (string, required): Session identifier

**Response**:
```json
{
  "session_id": "user-session-123",
  "history": [
    {
      "question": "What is AI?",
      "answer": "Artificial Intelligence refers to...",
      "timestamp": 1640995200
    },
    {
      "question": "How is it used in business?",
      "answer": "AI is used in business for...",
      "timestamp": 1640995260
    }
  ],
  "total_turns": 2
}
```

### Clear Conversation History

**DELETE** `/sessions/{session_id}/history`

Clear conversation history for a specific session.

**Parameters**:
- `session_id` (string, required): Session identifier

**Response**:
```json
{
  "message": "Conversation history cleared for session user-session-123",
  "session_id": "user-session-123"
}
```

## Error Handling

All endpoints return structured error responses:

```json
{
  "detail": "Error description",
  "error": "Error type or code",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Errors

| Error | Status | Description |
|-------|--------|-------------|
| `Question is required` | 400 | Empty question in chat request |
| `Question too long (max 1000 characters)` | 400 | Question exceeds character limit |
| `Unsupported file type` | 400 | File type not supported |
| `File too large` | 400 | File exceeds size limit |
| `No documents found` | 404 | No documents uploaded yet |
| `Service unavailable` | 503 | Backend components unhealthy |

## Rate Limiting

Default rate limits (configurable):
- Upload: 10 requests per minute
- Chat: 60 requests per minute
- Other endpoints: 100 requests per minute

## WebSocket Support

WebSocket endpoints for real-time features:

### Chat Streaming

**WS** `/ws/chat/{session_id}`

Real-time chat with streaming responses.

**Message Format**:
```json
{
  "type": "question",
  "content": "What is the document about?"
}
```

**Response Format**:
```json
{
  "type": "chunk",
  "content": "The document is about...",
  "accumulated": "The document is about..."
}
```

## SDK Examples

### Python

```python
import requests

# Upload document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
    print(response.json())

# Chat with document
response = requests.post(
    'http://localhost:8000/chat',
    json={
        'question': 'What is this document about?',
        'session_id': 'my-session'
    }
)
print(response.json())
```

### JavaScript

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('/upload', {
  method: 'POST',
  body: formData
});

// Chat with document
const chatResponse = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'What is this document about?',
    session_id: 'my-session'
  })
});
```

### cURL

```bash
# Upload document
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"

# Chat with document
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this about?",
    "session_id": "test-session"
  }'

# Get health status
curl -X GET "http://localhost:8000/health"
```

## Configuration

Environment variables affecting API behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (ollama/openai/huggingface) | `ollama` |
| `EMBEDDING_PROVIDER` | Embedding provider | `ollama` |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | `52428800` |
| `MAX_CHAT_HISTORY` | Maximum conversation turns stored | `10` |
| `RETRIEVAL_TOP_K` | Number of documents retrieved for context | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces provide:
- Interactive API testing
- Request/response examples
- Schema documentation
- Authentication testing

## Monitoring

### Metrics Endpoint

**GET** `/metrics`

Prometheus-compatible metrics for monitoring.

### Logging

All requests are logged with:
- Request ID
- Timestamp
- Method and endpoint
- Response status
- Processing time
- User session (if applicable)

Log format:
```
2024-01-01T00:00:00Z [INFO] REQUEST_ID=abc123 METHOD=POST PATH=/chat STATUS=200 DURATION=1.23s SESSION=user-123
```

## Security

### Input Validation

- File type validation
- File size limits
- Content sanitization
- SQL injection prevention
- XSS protection

### CORS

Configured to allow requests only from authorized origins:
```python
FRONTEND_ORIGINS=http://localhost:3000,https://your-domain.com
```

### Rate Limiting

Implemented to prevent abuse:
- Per-IP rate limiting
- Per-session rate limiting
- Global rate limiting

## Support

For API support:
- Check the interactive documentation at `/docs`
- Review logs for error details
- Verify health status at `/health`
- Check configuration variables