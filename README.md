# DocAI - Document AI Processing Platform

![Build Status](https://img.shields.io/badge/build-passing-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

DocAI is a modern document processing platform that enables users to upload documents and interact with them through AI-powered chat. Built with production-ready best practices and Docker containerization.

## ✨ Features

- 📄 **Document Upload**: Support for PDF, TXT, DOC, and DOCX files
- 💬 **AI Chat**: Intelligent conversation with your documents
- 🔒 **Security**: Environment-based configuration and CORS protection
- 🐳 **Docker Ready**: Full containerization with health checks
- 📊 **Monitoring**: Comprehensive logging and health endpoints
- 🎨 **Modern UI**: Responsive design with error handling
- ⚡ **Performance**: Optimized builds and caching

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │◄──►│    Backend      │◄──►│   Qdrant DB     │
│   (Next.js)     │    │   (FastAPI)     │    │  (Vector Store) │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      Port 3000             Port 8000             Port 6333
```

### Components

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.12
- **Vector Database**: Qdrant for document embeddings
- **Containerization**: Docker with multi-stage builds

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

### 2. Environment Configuration

Copy environment example files and configure them:

```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration  
cp frontend/.env.example frontend/.env
```

**Important**: Update the following environment variables in `backend/.env`:

```env
OPENAI_API_KEY=your_actual_openai_api_key
SECRET_KEY=your_secure_secret_key_here
QDRANT_API_KEY=your_qdrant_api_key  # Optional
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Qdrant**: http://localhost:6333

## 🛠️ Development Setup

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
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm start
```

## 📁 Project Structure

```
DocAI/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend container
│   └── .env.example        # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js app directory
│   │   ├── components/     # React components
│   │   └── lib/            # Utility functions
│   ├── Dockerfile          # Frontend container
│   ├── package.json        # Node.js dependencies
│   └── .env.example        # Frontend environment template
├── docker-compose.yml      # Container orchestration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI processing | Required |
| `QDRANT_HOST` | Qdrant database host | `qdrant` |
| `QDRANT_PORT` | Qdrant database port | `6333` |
| `FRONTEND_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `DocAI` |
| `NEXT_PUBLIC_MAX_FILE_SIZE` | Max upload size (bytes) | `10485760` |

## 🔒 Security Best Practices

- ✅ Environment variables for sensitive data
- ✅ CORS restricted to frontend domain only
- ✅ Input validation and file type restrictions
- ✅ Error logging without exposing internals
- ✅ Non-root containers in Docker
- ✅ Health checks for service monitoring

## 📊 Monitoring and Health Checks

### Health Endpoints

- **Backend**: `GET /health`
- **Frontend**: `GET /api/health`
- **Qdrant**: `GET /health`

### Docker Health Checks

All services include automated health checks:

```bash
# Check service status
docker-compose ps

# View health check logs
docker inspect <container_name> | grep -A 10 Health
```

## 🔍 API Documentation

### Upload Document

```http
POST /upload
Content-Type: multipart/form-data

{
  "file": <file>
}
```

### Chat with Documents

```http
POST /chat
Content-Type: application/json

{
  "question": "What is the main topic of the document?"
}
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚨 Error Handling

The application includes comprehensive error handling:

- **Frontend**: User-friendly error messages with retry options
- **Backend**: Structured error responses with logging
- **Network**: Timeout and connection error handling
- **Validation**: Input validation with clear feedback

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📝 Logging

Logs are structured and include:

- Request/response details
- Error tracking with stack traces
- Performance metrics
- Security events

View logs in development:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

## 🔄 Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **SSL/TLS**: Configure HTTPS with certificates
3. **Reverse Proxy**: Use Nginx or similar for load balancing
4. **Monitoring**: Integrate with monitoring solutions
5. **Backups**: Regular database and document backups

### Environment-Specific Builds

```bash
# Development
docker-compose -f docker-compose.yml up

# Production
docker-compose -f docker-compose.prod.yml up
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Container won't start:**
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
- Check file size limits
- Verify supported file types
- Review backend logs for errors

**Health check failures:**
```bash
# Manual health check
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

## 🔗 Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Docker Documentation](https://docs.docker.com/)

---

**Made with ❤️ for intelligent document processing**