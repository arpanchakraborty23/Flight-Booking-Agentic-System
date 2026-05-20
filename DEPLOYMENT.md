# AWS Deployment Guide

This guide explains how to deploy the Flight Booking Agentic System to AWS using Docker, ECR, and EC2.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured locally
3. EC2 instance running (Amazon Linux 2 or Ubuntu)
4. Docker and Docker Compose installed on EC2
5. GitHub repository with secrets configured

## AWS Infrastructure Setup

### 1. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name flight-booking-system \
  --region us-east-1
```

### 2. Create EC2 Instance

Launch an EC2 instance with:
- Amazon Linux 2 or Ubuntu 22.04+
- At least t3.medium (2 vCPU, 4GB RAM)
- Security group allowing ports 22, 8000, 8081-8083
- IAM role with EC2 and ECR permissions

### 3. Install Docker on EC2

```bash
# For Amazon Linux 2
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## GitHub Secrets Configuration

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

### AWS Credentials
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)

### API Keys
- `MISTRAL_API_KEY`: Mistral AI API key
- `AMADEUS_API_KEY`: Amadeus API key
- `AMADEUS_API_SECRET`: Amadeus API secret
- `LANGFUSE_SECRET_KEY`: Langfuse secret key (optional)
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key (optional)

### Voice Agent Keys
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `LIVEKIT_URL`: LiveKit WebSocket URL
- `MONGODB_URI`: MongoDB connection string (optional)
- `REDIS_URL`: Redis connection string (optional)

### Planner Agent Keys
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)

### EC2 Configuration
- `EC2_HOST`: Public IP or DNS of your EC2 instance
- `EC2_USERNAME`: EC2 username (ec2-user or ubuntu)
- `EC2_SSH_KEY`: Private SSH key for EC2 access
- `EC2_PORT`: SSH port (usually 22)

## Deployment Process

### Manual Deployment Steps

1. **Build Docker images locally:**
   ```bash
   docker build -t flight-booking-api .
   docker build -t voice-agent ./voice_agent
   docker build -t planner-agent ./planner_agent
   docker build -t mcp-server ./mcp
   ```

2. **Tag and push to ECR:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag images
   docker tag flight-booking-api:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:api-latest
   docker tag voice-agent:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:voice-agent-latest
   docker tag planner-agent:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:planner-agent-latest
   docker tag mcp-server:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:mcp-server-latest
   
   # Push images
   docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:api-latest
   docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:voice-agent-latest
   docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:planner-agent-latest
   docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:mcp-server-latest
   ```

3. **Deploy to EC2:**
   ```bash
   # Copy files to EC2
   scp -i your-key.pem docker-compose.yml .env ec2-user@<ec2-ip>:/home/ec2-user/flight-booking/
   
   # SSH to EC2
   ssh -i your-key.pem ec2-user@<ec2-ip>
   
   # Inside EC2:
   cd /home/ec2-user/flight-booking
   
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Pull images
   docker pull <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:api-latest
   docker pull <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:voice-agent-latest
   docker pull <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:planner-agent-latest
   docker pull <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/flight-booking-system:mcp-server-latest
   
   # Run services
   docker-compose up -d
   ```

### Automated Deployment (GitHub Actions)

The GitHub Actions workflow (`.github/workflows/build-deploy-ecr-ec2.yml`) automatically:

1. **On push/PR to main branch:**
   - Builds all Docker images
   - Pushes to ECR with version tags
   - Creates deployment package

2. **On push to main branch only:**
   - Transfers files to EC2
   - Executes deployment script
   - Verifies services are healthy

3. **Deployment verification:**
   - Checks if API responds on port 8000
   - Verifies all containers are running
   - Shows container logs if issues occur

## Monitoring and Debugging

### Check service status:
```bash
docker-compose ps
docker-compose logs
docker-compose logs -f api  # Specific service
docker-compose logs -f --tail=100  # Last 100 lines
```

### View container stats:
```bash
docker stats
```

### Restart services:
```bash
docker-compose restart
docker-compose restart api  # Specific service
```

### Update service:
```bash
docker-compose pull
docker-compose up -d --no-deps api  # Update specific service
```

## Health Checks

The deployment includes health checks for all services:
- API: http://localhost:8000/health
- Voice Agent: http://localhost:8081/health
- Planner Agent: http://localhost:8082/health
- MCP Server: http://localhost:8083/health

## Troubleshooting

### Issues with ECR login:
```bash
aws configure
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Docker daemon not running:
```bash
sudo service docker start
sudo systemctl enable docker
```

### Permission denied errors:
```bash
sudo usermod -a -G docker ec2-user
newgrp docker
```

### Clean up old images:
```bash
docker image prune -f
docker system prune -f
```

## Security Considerations

1. **Rotate AWS credentials regularly**
2. **Use IAM roles instead of access keys when possible**
3. **Limit ECR repository permissions**
4. **Use security groups to restrict access**
5. **Regularly update base images for security patches**
6. **Don't commit .env files to git**

## Cost Optimization

- Use spot instances for non-production deployments
- Set up lifecycle policies for ECR to clean old images
- Monitor EC2 usage and right-size instances
- Use AWS Cost Explorer to track spending
