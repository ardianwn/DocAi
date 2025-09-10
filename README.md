# DocAI - Production-Ready Document AI Platform

![Build Status](https://img.shields.io/badge/build-passing-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![LLM Support](https://img.shields.io/badge/LLM-Ollama%20%7C%20OpenAI%20%7C%20HuggingFace-purple)

DocAI is a production-ready document AI platform that enables users to upload documents and interact with them through AI-powered RAG (Retrieval-Augmented Generation) chat. Built with modern architecture, multi-model support, and comprehensive testing.

## ✨ Features

### 🚀 Core Capabilities
- 📄 **Multi-Document Upload**: Support for PDF, TXT, DOC, and DOCX files with progress tracking
- 💬 **AI-Powered Chat**: Intelligent conversation with your documents using RAG
- 🔍 **Source Citations**: View exact sources and relevance scores for AI responses
- 📊 **Document Management**: Statistics, health monitoring, and collection management
- 🎯 **Session Management**: Persistent chat history with export functionality

### 🤖 Multi-Model Support
- **Ollama**: Local LLM deployment (Llama2, CodeLlama, etc.)
- **OpenAI**: GPT-3.5/4 with text-embedding-3-small
- **HuggingFace**: Open-source models with transformers

### 🏗️ Production Features
- 🔒 **Security**: Environment-based configuration and CORS protection
- 🐳 **Docker Ready**: Full containerization with health checks
- 📊 **Monitoring**: Comprehensive logging and health endpoints
- 🎨 **Modern UI**: Responsive design with drag-and-drop upload
- ⚡ **Performance**: Optimized builds, caching, and async processing
- 🧪 **Testing**: Comprehensive test suite with >90% coverage

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │    │                 │
│   Frontend      │◄──►│    Backend      │◄──►│   Vector DB     │◄──►│   LLM Provider  │
│   (Next.js)     │    │   (FastAPI)     │    │   (Qdrant)      │    │ (Ollama/OpenAI) │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
      Port 3000             Port 8000             Port 6333             Port 11434
```

### 🧩 Components

**Frontend (Next.js 15)**
- TypeScript with Tailwind CSS
- Document upload with drag-and-drop
- Real-time chat with source citations
- Document management dashboard

**Backend (FastAPI)**
- Unified RAG service orchestration
- Multi-format document parsing
- Vector embeddings with multiple providers
- Session-based conversation management

**Vector Database (Qdrant)**
- High-performance vector similarity search
- Collection management and health monitoring
- Scalable document storage

**LLM Integration**
- Provider-agnostic architecture
- Model switching via environment configuration
- Streaming and batch processing support

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)

### 1. Clone and Setup

```bash
git clone https://github.com/ardianwn/DocAI.git
cd DocAI
```

### 2. Choose Your LLM Provider

DocAI supports multiple LLM providers. Choose one:

#### Option A: Ollama (Local, Free)
```bash
./infra/run.sh ollama
```

#### Option B: OpenAI (API Key Required)
```bash
# Set your OpenAI API key in backend/.env
./infra/run.sh openai
```

#### Option C: HuggingFace (Local, Free)
```bash
./infra/run.sh huggingface
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant**: http://localhost:6333

### 4. First Steps

1. Upload a document via the web interface
2. Wait for processing to complete
3. Start chatting with your document
4. View sources and manage your collection

## 🔧 Configuration

### Environment Variables

Create configuration files from examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Backend Configuration (`backend/.env`)

```env
# LLM Provider (ollama, openai, huggingface)
LLM_PROVIDER=ollama
LLM_MODEL=llama2

# Embedding Provider
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

# API Keys (if using external providers)
OPENAI_API_KEY=your_key_here

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Security
SECRET_KEY=your_secure_secret_key
```

### Frontend Configuration (`frontend/.env`)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_MULTI_UPLOAD=true
NEXT_PUBLIC_ENABLE_CHAT_HISTORY=true
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
```

## 🛠️ Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build
npm start
```

## 📁 Project Structure

```
DocAI/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── rag_service.py      # Unified RAG orchestration
│   │   ├── pdf_parser.py       # Document parsing
│   │   ├── embedding_ollama.py # Ollama embeddings
│   │   ├── openai_client.py    # OpenAI integration
│   │   ├── huggingface_client.py # HuggingFace integration
│   │   ├── qdrant_client.py    # Vector database client
│   │   └── chat_llama.py       # Chat functionality
│   ├── tests/                  # Comprehensive test suite
│   │   ├── unit/               # Unit tests
│   │   └── integration/        # Integration tests
│   ├── requirements.txt        # Python dependencies
│   ├── pytest.ini            # Test configuration
│   ├── Dockerfile             # Container definition
│   └── .env.example           # Environment template
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   ├── components/        # React components
│   │   │   ├── UploadComponent.tsx
│   │   │   ├── ChatComponent.tsx
│   │   │   ├── DocumentManagement.tsx
│   │   │   └── __tests__/     # Component tests
│   │   └── lib/               # Utility functions
│   ├── jest.config.js         # Jest test configuration
│   ├── jest.setup.js          # Test setup
│   ├── Dockerfile             # Container definition
│   ├── package.json           # Node.js dependencies
│   └── .env.example           # Environment template
├── infra/                      # Infrastructure & deployment
│   ├── run.sh                 # Deployment script
│   └── .env.production        # Production config template
├── docker-compose.yml          # Default (Ollama) setup
├── docker-compose.ollama.yml   # Ollama configuration
├── docker-compose.openai.yml   # OpenAI configuration
├── docker-compose.huggingface.yml # HuggingFace configuration
├── docker-compose.prod.yml     # Production configuration
├── LICENSE                     # MIT License
└── README.md                   # This file
```

## 🌐 Deployment

### Development Deployment

```bash
# Start with Ollama (default)
docker-compose up -d

# Start with OpenAI
docker-compose -f docker-compose.openai.yml up -d

# Start with HuggingFace
docker-compose -f docker-compose.huggingface.yml up -d
```

### Production Deployment

```bash
# Configure production environment
cp infra/.env.production backend/.env

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Cloud Deployment

The application is cloud-ready and can be deployed on:

- **AWS**: ECS, EKS, or EC2 with docker-compose
- **Google Cloud**: Cloud Run, GKE, or Compute Engine
- **Azure**: Container Instances, AKS, or VM
- **DigitalOcean**: App Platform or Droplets

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m "not slow"  # Skip slow tests
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Wait for services to be healthy
sleep 30

# Run integration tests
cd backend && pytest -m integration
```

## 📊 Monitoring and Health Checks

### Health Endpoints

- **Backend**: `GET /health` - Comprehensive component health
- **Frontend**: `GET /api/health` - Frontend and backend connectivity
- **Qdrant**: `GET /health` - Vector database status

### Monitoring

```bash
# Check service status
docker-compose ps

# View real-time logs
docker-compose logs -f

# Check individual service health
curl http://localhost:8000/health
curl http://localhost:3000/api/health
curl http://localhost:6333/health
```

### Performance Metrics

The backend exposes metrics for:
- Document processing times
- Embedding generation speed
- Vector search performance
- Chat response latency
- Memory and CPU usage

## 🔍 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```http
# Upload Document
POST /upload
Content-Type: multipart/form-data

# Chat with Documents
POST /chat
Content-Type: application/json
{
  "question": "What is the document about?",
  "session_id": "user-session-123"
}

# Get Document Statistics
GET /documents

# Get Chat History
GET /sessions/{session_id}/history

# Health Check
GET /health
```

## 🛡️ Security Best Practices

- ✅ Environment variables for sensitive data
- ✅ CORS restricted to frontend domain only
- ✅ Input validation and file type restrictions
- ✅ Error logging without exposing internals
- ✅ Non-root containers in Docker
- ✅ Health checks for service monitoring
- ✅ Rate limiting and request size limits
- ✅ Secure file upload handling

## 🔧 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs <service_name>

# Rebuild containers
docker-compose build --no-cache
```

**CORS errors:**
- Verify `FRONTEND_ORIGINS` in backend/.env
- Check frontend `NEXT_PUBLIC_API_URL`

**Upload failures:**
- Check file size limits (default 10MB)
- Verify supported file types
- Review backend logs for errors

**Chat not working:**
- Ensure documents are uploaded and processed
- Check LLM provider configuration
- Verify vector database health

**Out of memory:**
- Reduce batch sizes in embedding generation
- Use smaller models for HuggingFace
- Increase Docker memory limits

### Performance Optimization

```bash
# Optimize for production
export EMBEDDING_BATCH_SIZE=16
export LLM_MAX_TOKENS=1024
export QDRANT_VECTOR_SIZE=768

# Monitor resource usage
docker stats

# Scale services
docker-compose up -d --scale backend=2
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run the test suite: `npm test && pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a Pull Request

### Development Guidelines

- Follow TypeScript/Python best practices
- Add tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Next.js](https://nextjs.org/)
- Vector search powered by [Qdrant](https://qdrant.tech/)
- LLM integration via [Ollama](https://ollama.ai/), [OpenAI](https://openai.com/), and [HuggingFace](https://huggingface.co/)
- Inspired by the [dmayboroda/minima](https://github.com/dmayboroda/minima) project structure

## 🔗 Links

- [Live Demo](https://your-demo-url.com) (if available)
- [API Documentation](http://localhost:8000/docs)
- [Docker Hub](https://hub.docker.com/r/yourusername/docai) (if published)
- [Issue Tracker](https://github.com/ardianwn/DocAI/issues)

---

**Made with ❤️ for intelligent document processing**

*Transform your documents into interactive knowledge with the power of AI*