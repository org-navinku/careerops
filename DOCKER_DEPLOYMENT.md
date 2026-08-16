# Docker & ECR Deployment Guide

## Overview

CareerOps is now containerized and ready for deployment to AWS ECR (Elastic Container Registry).

## Prerequisites

- Docker installed locally
- AWS CLI configured
- AWS account with ECR permissions
- LLM provider API key (OpenAI, Anthropic, or custom — configured in-app)

## Local Docker Build & Test

### 1. Build the Docker image locally

```bash
cd /path/to/careerops

# Build the image
docker build -t careerops:latest .

# Or with a specific tag
docker build -t careerops:v1.0 .
```

### 2. Test locally with docker-compose

```bash
# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f careerops

# Stop the service
docker-compose down
```

### 3. Test the image manually

```bash
# Run the container
docker run -d \
  --name careerops \
  -p 5001:5001 \
  -p 8000:8000 \
  -e OLLAMA_BASE=http://host.docker.internal:11434 \
  careerops:latest

# Check if it's running
curl http://localhost:5001/api/health

# View logs
docker logs -f careerops

# Stop and remove
docker stop careerops
docker rm careerops
```

## Push to AWS ECR

### 1. Create ECR repository

```bash
# Set variables
AWS_REGION="us-east-2"  # Change as needed
ECR_REPO_NAME="careerops"

# Create repository
aws ecr create-repository \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION
```

### 2. Authenticate Docker with ECR

```bash
# Get login token and authenticate
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
```

### 3. Tag the image for ECR

```bash
# Get your AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Tag the local image
docker tag careerops:latest $ECR_URI:latest
docker tag careerops:latest $ECR_URI:v1.0
```

### 4. Push to ECR

```bash
# Push images
docker push $ECR_URI:latest
docker push $ECR_URI:v1.0

# Verify push
aws ecr describe-images --repository-name $ECR_REPO_NAME --region $AWS_REGION
```

## Deploy from ECR

### Option 1: Using ECS Fargate

```bash
# Create ECS task definition (use the ECR URI from above)
# Reference: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/careerops:latest

# In AWS Console:
# 1. Go to ECS > Task Definitions > Create new
# 2. Set container image to your ECR URI
# 3. Set port mappings: 5001, 8000
# 4. Set environment variables:
#    - OLLAMA_BASE=http://ollama-endpoint:11434
#    - OLLAMA_MODEL=mistral
# 5. Create service from task definition
```

### Option 2: Using EKS (Kubernetes)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: careerops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: careerops
  template:
    metadata:
      labels:
        app: careerops
    spec:
      containers:
      - name: careerops
        image: ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/careerops:latest
        ports:
        - containerPort: 5001
          name: backend
        - containerPort: 8000
          name: frontend
        env:
        - name: OLLAMA_BASE
          value: "http://ollama-service:11434"
        - name: OLLAMA_MODEL
          value: "mistral"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: careerops
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    name: http
  - port: 5001
    targetPort: 5001
    name: api
  selector:
    app: careerops

# Deploy:
# kubectl apply -f deployment.yaml
```

## Environment Variables

Supported environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | 5001 | Backend API port |
| `FLASK_ENV` | production | Flask environment |
| `OLLAMA_BASE` | http://localhost:11434 | Ollama service URL |
| `OLLAMA_MODEL` | mistral | Ollama model to use |

## Building Multi-Architecture Images

For ARM and x86 support (Mac M1/M2 compatibility):

```bash
# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $ECR_URI:latest \
  -t $ECR_URI:v1.0 \
  --push \
  .
```

## Automated CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/build-push.yml
name: Build and Push to ECR

on:
  push:
    branches: [main]
    paths:
      - 'careerops/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-2

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: careerops
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                     $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs careerops

# Verify image
docker inspect careerops:latest

# Run with explicit command
docker run -it careerops:latest /bin/bash
```

### Health check failing
```bash
# The health check verifies DynamoDB connectivity
# Ensure AWS credentials are available to the container
# (via env vars, IAM role, or mounted ~/.aws/credentials)
```

### ECR push fails
```bash
# Verify authentication
aws ecr get-authorization-token --region $AWS_REGION

# Check repository exists
aws ecr describe-repositories --region $AWS_REGION

# Verify permissions
aws iam get-user
```

## Security Best Practices

- Use multi-stage builds (already implemented)
- Run as non-root user (careerops:1000)
- Scan images for vulnerabilities: `aws ecr start-image-scan`
- Use private ECR repository (not public)
- Enable ECR image encryption
- Use VPC endpoints for ECR access
- Set resource limits (CPU/Memory)
- Enable container logging

## Performance Tips

- Use `.dockerignore` to reduce image size
- Keep image layers minimal
- Use health checks appropriately
- Set resource requests/limits
- Use multi-architecture builds
- Cache docker layers efficiently

## Cleanup

```bash
# Remove local images
docker rmi careerops:latest

# Remove ECR repository (WARNING: deletes all images)
aws ecr delete-repository \
  --repository-name careerops \
  --force \
  --region $AWS_REGION
```

## Next Steps

1. Build and test locally: `docker-compose up`
2. Push to ECR: Follow push to ECR steps above
3. Deploy to ECS or EKS: Use your preferred deployment method
4. Monitor: Set up CloudWatch logs for container output
5. Scale: Use auto-scaling groups or Kubernetes HPA

---

**Need help?** Check the main README.md or SETUP.md for additional context.
