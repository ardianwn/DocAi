# DocAI Deployment Guide

This guide covers various deployment scenarios for DocAI, from development to production environments.

## Table of Contents

- [Quick Development Setup](#quick-development-setup)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Scaling and Load Balancing](#scaling-and-load-balancing)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Quick Development Setup

### Prerequisites

- Docker and Docker Compose
- Git
- At least 4GB RAM
- 10GB free disk space

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/ardianwn/DocAI.git
cd DocAI

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Choose Your LLM Provider

#### Option A: Ollama (Recommended for Development)

```bash
# Start with Ollama
./infra/run.sh ollama

# Wait for services to start (2-3 minutes)
docker-compose -f docker-compose.ollama.yml logs -f
```

First time setup will pull required models:
```bash
# Pull required models (run after containers are up)
docker exec -it docai-ollama ollama pull llama2
docker exec -it docai-ollama ollama pull nomic-embed-text
```

#### Option B: OpenAI (Fastest Setup)

```bash
# Edit backend/.env and add your OpenAI API key
echo "OPENAI_API_KEY=your_actual_api_key_here" >> backend/.env

# Start with OpenAI
./infra/run.sh openai
```

#### Option C: HuggingFace (Free but Resource Intensive)

```bash
# Start with HuggingFace (requires ~8GB RAM)
./infra/run.sh huggingface
```

### 3. Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/api/health

# Access the application
open http://localhost:3000
```

## Production Deployment

### Environment Preparation

1. **Server Requirements**:
   - Linux server (Ubuntu 20.04+ recommended)
   - 8GB+ RAM (16GB for HuggingFace models)
   - 50GB+ SSD storage
   - Docker and Docker Compose installed

2. **Security Setup**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Create non-root user for Docker
sudo usermod -aG docker $USER
```

### Production Configuration

1. **Environment Variables**:
```bash
# Copy production template
cp infra/.env.production backend/.env

# Edit with secure values
nano backend/.env
```

Required changes:
```env
# Use strong secret keys
SECRET_KEY=your_very_secure_production_secret_key_64_characters_long

# Production API keys
OPENAI_API_KEY=your_production_openai_key

# Production URLs
FRONTEND_ORIGINS=https://your-domain.com

# Secure logging
LOG_LEVEL=WARNING

# Production vector store
QDRANT_API_KEY=your_production_qdrant_key
```

2. **SSL/TLS Setup**:
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificates
sudo certbot certonly --standalone -d your-domain.com
```

3. **Nginx Configuration**:
```nginx
# /etc/nginx/sites-available/docai
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File upload limits
    client_max_body_size 50M;
}
```

### Deploy with Production Configuration

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor startup
docker-compose -f docker-compose.prod.yml logs -f

# Verify deployment
curl https://your-domain.com/api/health
```

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Create ECS Cluster**:
```bash
# Install AWS CLI
aws configure

# Create cluster
aws ecs create-cluster --cluster-name docai-cluster
```

2. **Push Images to ECR**:
```bash
# Create repositories
aws ecr create-repository --repository-name docai-backend
aws ecr create-repository --repository-name docai-frontend

# Build and push images
docker build -t docai-backend ./backend
docker build -t docai-frontend ./frontend

# Tag and push
docker tag docai-backend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/docai-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/docai-backend:latest
```

3. **Create Task Definition**:
```json
{
  "family": "docai-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "docai-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/docai-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_PROVIDER",
          "value": "openai"
        }
      ]
    }
  ]
}
```

#### Using EC2 with Docker Compose

```bash
# Launch EC2 instance (t3.large recommended)
# Connect via SSH

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -a -G docker ec2-user

# Clone and deploy
git clone https://github.com/ardianwn/DocAI.git
cd DocAI
./infra/run.sh openai
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Deploy**:
```bash
# Configure gcloud
gcloud config set project your-project-id

# Build backend
gcloud builds submit --tag gcr.io/your-project-id/docai-backend ./backend

# Deploy backend
gcloud run deploy docai-backend \
  --image gcr.io/your-project-id/docai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi

# Build and deploy frontend
gcloud builds submit --tag gcr.io/your-project-id/docai-frontend ./frontend
gcloud run deploy docai-frontend \
  --image gcr.io/your-project-id/docai-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Using GKE (Google Kubernetes Engine)

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docai-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docai-backend
  template:
    metadata:
      labels:
        app: docai-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project-id/docai-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_PROVIDER
          value: "openai"
---
apiVersion: v1
kind: Service
metadata:
  name: docai-backend-service
spec:
  selector:
    app: docai-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name docai-rg --location eastus

# Deploy backend container
az container create \
  --resource-group docai-rg \
  --name docai-backend \
  --image your-registry/docai-backend:latest \
  --dns-name-label docai-backend \
  --ports 8000 \
  --memory 2 \
  --cpu 1

# Deploy frontend container
az container create \
  --resource-group docai-rg \
  --name docai-frontend \
  --image your-registry/docai-frontend:latest \
  --dns-name-label docai-frontend \
  --ports 3000 \
  --memory 1 \
  --cpu 1
```

### DigitalOcean Deployment

#### Using App Platform

```yaml
# .do/app.yaml
name: docai
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/DocAI
    branch: main
  run_command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: LLM_PROVIDER
    value: openai
  - key: OPENAI_API_KEY
    value: ${OPENAI_API_KEY}

- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/DocAI
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
```

## Scaling and Load Balancing

### Horizontal Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Use Nginx for load balancing
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

### Database Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:v1.7.0
    deploy:
      replicas: 2
    environment:
      - QDRANT__CLUSTER__ENABLED=true
```

### Caching Layer

```yaml
# Add Redis for caching
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

## Monitoring and Maintenance

### Health Monitoring

```bash
# Create health check script
#!/bin/bash
# health-check.sh

BACKEND_URL="http://localhost:8000/health"
FRONTEND_URL="http://localhost:3000/api/health"

if curl -f $BACKEND_URL >/dev/null 2>&1; then
    echo "Backend: OK"
else
    echo "Backend: FAIL"
    # Restart backend
    docker-compose restart backend
fi

if curl -f $FRONTEND_URL >/dev/null 2>&1; then
    echo "Frontend: OK"
else
    echo "Frontend: FAIL"
    docker-compose restart frontend
fi
```

### Log Management

```bash
# Configure log rotation
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup Qdrant data
docker run --rm \
  -v docai_qdrant_data:/source \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz -C /source .

# Backup uploaded documents
docker run --rm \
  -v docai_uploaded_docs:/source \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/docs-$(date +%Y%m%d).tar.gz -C /source .

# Upload to cloud storage
aws s3 cp backups/ s3://your-backup-bucket/ --recursive
```

### Update Strategy

```bash
#!/bin/bash
# update.sh

# Pull latest images
docker-compose pull

# Backup before update
./backup.sh

# Rolling update
docker-compose up -d --no-deps backend
sleep 30
docker-compose up -d --no-deps frontend

# Verify health
./health-check.sh
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
docker-compose logs --tail=50 backend
docker-compose logs --tail=50 frontend

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Monitor system resources
htop

# Check Qdrant performance
curl http://localhost:6333/metrics
```

#### Network Issues

```bash
# Test connectivity
docker-compose exec backend ping qdrant
docker-compose exec frontend ping backend

# Check port conflicts
netstat -tulpn | grep :8000
```

### Recovery Procedures

#### Database Corruption

```bash
# Stop services
docker-compose down

# Restore from backup
docker run --rm \
  -v $(pwd)/backups:/backup \
  -v docai_qdrant_data:/target \
  alpine tar xzf /backup/qdrant-latest.tar.gz -C /target

# Restart services
docker-compose up -d
```

#### Complete System Recovery

```bash
# Full system restore
docker-compose down -v  # Remove all volumes
./restore-from-backup.sh
docker-compose up -d
```

### Monitoring Alerts

Set up alerts for:
- Service health failures
- High memory usage (>80%)
- High disk usage (>85%)
- Response time > 5 seconds
- Error rate > 5%

Example monitoring with Prometheus:
```yaml
# prometheus.yml
rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Support and Maintenance

- Monitor logs daily
- Update security patches monthly
- Backup data weekly
- Test recovery procedures quarterly
- Review and rotate API keys quarterly

For additional support:
- Check GitHub issues
- Review documentation
- Monitor health endpoints
- Contact system administrators