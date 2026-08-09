#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
ECR_REPO_NAME=${ECR_REPO_NAME:-careerops}
IMAGE_TAG=${IMAGE_TAG:-latest}
LOCAL_IMAGE_NAME="careerops"

echo -e "${YELLOW}🚀 CareerOps ECR Deployment Script${NC}\n"

# Step 1: Get AWS Account ID
echo -e "${YELLOW}Step 1: Getting AWS Account ID...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$ACCOUNT_ID" ]; then
  echo -e "${RED}❌ Failed to get AWS Account ID. Make sure AWS CLI is configured.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Account ID: $ACCOUNT_ID${NC}\n"

# Step 2: Set ECR URI
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
echo -e "${YELLOW}Step 2: ECR Repository URI${NC}"
echo -e "${GREEN}✓ ECR URI: $ECR_URI${NC}\n"

# Step 3: Check if repository exists
echo -e "${YELLOW}Step 3: Checking if ECR repository exists...${NC}"
if aws ecr describe-repositories \
  --repository-names $ECR_REPO_NAME \
  --region $AWS_REGION >/dev/null 2>&1; then
  echo -e "${GREEN}✓ Repository exists${NC}\n"
else
  echo -e "${YELLOW}⚠ Repository does not exist. Creating...${NC}"
  aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION
  echo -e "${GREEN}✓ Repository created${NC}\n"
fi

# Step 4: Build Docker image
echo -e "${YELLOW}Step 4: Building Docker image...${NC}"
docker build -t $LOCAL_IMAGE_NAME:$IMAGE_TAG .
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Image built successfully${NC}\n"
else
  echo -e "${RED}❌ Docker build failed${NC}"
  exit 1
fi

# Step 5: Authenticate with ECR
echo -e "${YELLOW}Step 5: Authenticating with ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URI
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Authenticated with ECR${NC}\n"
else
  echo -e "${RED}❌ ECR authentication failed${NC}"
  exit 1
fi

# Step 6: Tag image for ECR
echo -e "${YELLOW}Step 6: Tagging image for ECR...${NC}"
docker tag $LOCAL_IMAGE_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $LOCAL_IMAGE_NAME:$IMAGE_TAG $ECR_URI:latest
echo -e "${GREEN}✓ Image tagged${NC}\n"

# Step 7: Push to ECR
echo -e "${YELLOW}Step 7: Pushing image to ECR...${NC}"
echo "Pushing $ECR_URI:$IMAGE_TAG..."
docker push $ECR_URI:$IMAGE_TAG
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Pushed $ECR_URI:$IMAGE_TAG${NC}"
else
  echo -e "${RED}❌ Push failed${NC}"
  exit 1
fi

echo "Pushing $ECR_URI:latest..."
docker push $ECR_URI:latest
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Pushed $ECR_URI:latest${NC}\n"
else
  echo -e "${RED}❌ Push failed${NC}"
  exit 1
fi

# Step 8: Verify push
echo -e "${YELLOW}Step 8: Verifying images in ECR...${NC}"
aws ecr describe-images \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes,imagePushedAt]' \
  --output table

echo -e "\n${GREEN}✅ Successfully pushed to ECR!${NC}\n"
echo -e "${GREEN}Image URI: $ECR_URI:$IMAGE_TAG${NC}"
echo -e "${GREEN}Latest URI: $ECR_URI:latest${NC}\n"

# Print next steps
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Deploy to ECS/EC2/EKS using the image URI above"
echo "2. Set environment variables for Ollama connection"
echo "3. Configure security groups and IAM roles"
echo "4. Monitor container logs in CloudWatch"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "# View image details"
echo "aws ecr describe-images --repository-name $ECR_REPO_NAME --region $AWS_REGION"
echo ""
echo "# Pull image locally"
echo "docker pull $ECR_URI:latest"
echo ""
echo "# Delete repository"
echo "aws ecr delete-repository --repository-name $ECR_REPO_NAME --force --region $AWS_REGION"
