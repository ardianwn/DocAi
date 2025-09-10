#!/bin/bash

# DocAI Run Script - Start DocAI with specified model provider
# Usage: ./run.sh [ollama|openai|huggingface]

set -e

PROVIDER=${1:-ollama}
COMPOSE_FILE=""

case $PROVIDER in
    ollama)
        COMPOSE_FILE="docker-compose.ollama.yml"
        echo "🚀 Starting DocAI with Ollama (Local Models)"
        ;;
    openai)
        COMPOSE_FILE="docker-compose.openai.yml"
        echo "🚀 Starting DocAI with OpenAI API"
        ;;
    huggingface)
        COMPOSE_FILE="docker-compose.huggingface.yml"
        echo "🚀 Starting DocAI with HuggingFace Models"
        ;;
    *)
        echo "❌ Invalid provider. Use: ollama, openai, or huggingface"
        exit 1
        ;;
esac

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if environment files exist
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your API keys and configuration"
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  frontend/.env not found. Copying from .env.example..."
    cp frontend/.env.example frontend/.env
fi

echo "📋 Using compose file: $COMPOSE_FILE"

# Start services
docker compose -f $COMPOSE_FILE up -d

echo "✅ DocAI is starting up..."
echo ""
echo "📊 Service Status:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Qdrant: http://localhost:6333"

if [ "$PROVIDER" = "ollama" ]; then
    echo "   Ollama: http://localhost:11434"
    echo ""
    echo "📦 To pull Ollama models, run:"
    echo "   docker exec -it docai-ollama ollama pull llama2"
    echo "   docker exec -it docai-ollama ollama pull nomic-embed-text"
fi

echo ""
echo "📝 To view logs: docker compose -f $COMPOSE_FILE logs -f"
echo "🛑 To stop: docker compose -f $COMPOSE_FILE down"