# CORA POC Infrastructure

Lightweight AWS infrastructure for running CORA on a single EC2 instance with Cloudflare Tunnel for browser access and Google authentication.

## Overview

This POC infrastructure is designed for quick deployment and teardown of the CORA application without the complexity of a full production setup (ECS, RDS, etc.).

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      EC2 (t3.micro)                         │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐      │
│  │  FastAPI   │   │  Next.js    │   │ Cloudflared  │      │
│  │  (port 8000)│   │  (port 3000)│   │   Tunnel     │      │
│  └─────────────┘   └─────────────┘   └──────────────┘      │
│         │                │                   │              │
│         └────────────────┴───────────────────┘              │
│                          │                                  │
│                    Docker Compose                           │
└─────────────────────────────────────────────────────────────┘
              │                           │
              │ HTTPS                     │
              ▼                           │
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare Zero Trust                          │
│         (Google Auth + Access Policy)                      │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
    User's Browser (https://cora-*.trycloudflare.com)
```

### Key Features

- **Single EC2 Instance**: Runs both FastAPI and Next.js containers
- **Cloudflare Tunnel**: Provides public URL without needing a domain
- **Google Authentication**: Restricts access to specific email domains
- **Cross-Account Access**: EC2 can access resources in another AWS account
- **CloudWatch Logs**: 7-day log retention
- **Easy Start/Stop**: Data persists on EBS, can stop/start anytime

## Files

| File | Description |
|------|-------------|
| `iac/cloudformation/poc-template.yaml` | CloudFormation template (full stack) |
| `iac/cloudformation/docker-compose.yml` | Docker Compose for FastAPI + Next.js |
| `iac/cloudformation/user-data.sh` | Standalone user data script (manual EC2) |
| `iac/cloudformation/README.md` | Quick reference guide |

## Prerequisites

### 1. Docker Images

Push your Docker images to Docker Hub (or any registry):

```bash
# Build and push API image
docker build -t youruser/cora:latest .
docker push youruser/cora:latest

# Build and push Client image
cd client
docker build -t youruser/cora-client:latest .
docker push youruser/cora-client:latest
```

### 2. Cloudflare Account

1. Create a free [Cloudflare account](https://dash.cloudflare.com)
2. Go to Zero Trust → Overview → Sign up for Zero Trust
3. Note your **Team Name** (e.g., `your-team`)

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Go to APIs & Services → Credentials
4. Configure OAuth consent screen:
   - User Type: External
   - Fill in required fields
5. Create Credentials → OAuth client ID:
   - Application type: Web application
   - Authorized JavaScript origins: `https://<your-team>.cloudflareaccess.com`
   - Authorized redirect URIs: `https://<your-team>.cloudflareaccess.com/cdn-cgi/access/callback`
6. Copy the **Client ID** and **Client Secret**

### 4. Cloudflare Zero Trust Setup

1. Go to Zero Trust → Access → Applications
2. Add application → Self-hosted
3. Configure:
   - Application name: `CORA`
   - Session duration: 24 hours
   - Domain: `*.trycloudflare.com`
4. Add authentication:
   - Settings → Authentication → Add new → Google
   - Enter your Google Client ID and Secret
5. Create access policy:
   - Name: `Allow Google Users`
   - Action: Allow
   - Rule: Email → ends with → `@yourcompany.com` (or `@gmail.com`)

### 5. Create Cloudflare Tunnel

1. Go to Zero Trust → Networks → Tunnels
2. Add tunnel → Create a new tunnel
3. Name: `cora-poc`
4. Copy the **Tunnel Token** (not the tunnel ID)

## Deployment

### Option 1: CloudFormation (Recommended)

1. Create your `.env.aws` file:
   ```bash
   cp iac/cloudformation/.env.aws.example .env.aws
   # Edit .env.aws with your values
   ```

2. Encode to base64:
   ```bash
   ENV_FILE=$(base64 -w0 .env.aws)
   ```

3. Deploy:
   ```bash
   aws cloudformation deploy \
     --template-file iac/cloudformation/poc-template.yaml \
     --stack-name cora-poc \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides \
       AccountId=123456789012 \
       DockerImageApi=youruser/cora:latest \
       DockerImageClient=youruser/cora-client:latest \
       CloudflareToken=your-cloudflare-tunnel-token \
       KeyPairName=your-key-pair-name \
       EnvFileBase64="$ENV_FILE"
   ```

### Option 2: Manual EC2 Launch

1. Launch an EC2 instance:
   - AMI: Amazon Linux 2023
   - Type: t3.micro
   - Security Group: Allow ports 22, 3000, 8000

2. Create `.env.aws` file and encode:
   ```bash
   ENV_FILE=$(base64 -w0 .env.aws)
   ```

3. Run user data script:
   ```bash
   curl -sL https://raw.githubusercontent.com/yourrepo/main/iac/cloudformation/user-data.sh | \
     DOCKER_IMAGE_API=youruser/cora:latest \
     DOCKER_IMAGE_CLIENT=youruser/cora-client:latest \
     CLOUDFLARE_TOKEN=your-token \
     ENV_FILE_BASE64="$ENV_FILE" \
     bash
   ```

## Getting the URL

After deployment:

```bash
# SSH to EC2
ssh -i your-key.pem ec2-user@<elastic-ip>

# Check tunnel logs
cat /var/log/cloudflared.log
```

Look for a line like:
```
https://cora-abc123.trycloudflare.com
```

Visit this URL and sign in with your Google account.

## Cross-Account Access

To allow EC2 (Account 1) to access AWS resources in another account (Account 2):

### Step 1: Configure Role in Account 2

1. Go to IAM → Roles → Select your existing role
2. Edit **Trust Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT1:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Step 2: Deploy with Cross-Account Role

Pass the role ARN as a parameter:
```bash
--parameter-overrides \
  CrossAccountRoleArn=arn:aws:iam::ACCOUNT2:role/YourRoleName
```

The app automatically uses this role - no `--profile` flag needed.

## Environment Variables

All environment variables are stored in the `.env.aws` file. Copy the template and fill in your values:

```bash
cp iac/cloudformation/.env.aws.example .env.aws
# Edit .env.aws with your values
```

Note: LLM and Langfuse keys are handled by the app via `~/.cora/config.yaml` - no need to pass them here.

### .env.aws Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DOCKER_HUB_USERNAME` | Docker Hub username | No (only if private images) |
| `DOCKER_HUB_ACCESS_TOKEN` | Docker Hub Personal Access Token | No |
| `AWS_ROLE_ARN` | Cross-account role ARN | No |
| `MODAL_TOKEN_ID` | Modal Token ID | No |
| `MODAL_TOKEN_SECRET` | Modal Token Secret | No |

## CloudFormation Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `AccountId` | AWS Account ID | Yes |
| `DockerImageApi` | API Docker image | Yes |
| `DockerImageClient` | Client Docker image | Yes |
| `CloudflareToken` | Cloudflare Tunnel token | Yes |
| `EnvFileBase64` | Base64 encoded .env.aws content | Yes |
| `KeyPairName` | EC2 Key Pair name | No |
| `InstanceType` | EC2 instance type (default: t3.micro) | No |

## Operations

### Start (Bring Up)

```bash
# Start the EC2 instance
aws ec2 start-instances --instance-id <instance-id>
```

### Stop (Bring Down)

```bash
# Stop the EC2 instance (data persists on EBS)
aws ec2 stop-instances --instance-id <instance-id>
```

### Destroy

```bash
# Delete CloudFormation stack (all resources gone)
aws cloudformation delete-stack --stack-name cora-poc
```

### View Logs

```bash
# CloudWatch Logs
aws logs tail /aws/ec2/cora-poc --follow

# Or SSH and check local logs
ssh ec2-user@<ip> "tail -f /var/log/cloudflared.log"
ssh ec2-user@<ip> "docker logs cora-api"
ssh ec2-user@<ip> "docker logs cora-client"
```

## Cost

| Resource | Cost (us-east-1) |
|----------|------------------|
| EC2 t3.micro | ~$8/month |
| EBS (8GB) | ~$1/month |
| Data transfer | ~$1/month |
| **Total** | **~$10/month** |

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker ps

# Check container logs
docker logs cora-api
docker logs cora-client

# Check docker-compose
cd /opt/cora
docker-compose logs
```

### Cloudflare Tunnel Not Working

```bash
# Check tunnel logs
cat /var/log/cloudflared.log

# Verify tunnel is running
ps aux | grep cloudflared

# Restart tunnel
pkill cloudflared
nohup cloudflared tunnel --url http://localhost:3000 --token "$CLOUDFLARE_TOKEN" > /var/log/cloudflared.log 2>&1 &
```

### Can't Access URL

1. Check Cloudflare Access Policy allows your email
2. Verify tunnel is running: `ps aux | grep cloudflared`
3. Check Security Group allows outbound 443
4. Verify Google OAuth is configured correctly in Cloudflare Zero Trust

### Cross-Account Not Working

1. Verify trust policy in Account 2 allows Account 1
2. Check EC2 IAM role has permission to assume the role
3. Verify the role ARN is correct

## Security

- **IAM Role**: Instance has `ReadOnlyAccess` on AWS resources
- **Access Control**: Cloudflare Zero Trust with Google authentication
- **Policy**: Restrict to `@yourcompany.com` or `@gmail.com`
- **SSH**: Key-based authentication only

## Files Reference

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    image: ${DOCKER_IMAGE_API}
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=${AWS_REGION}
      - AWS_ROLE_ARN=${AWS_ROLE_ARN}
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL_ID=${LLM_MODEL_ID}
    restart: unless-stopped

  client:
    image: ${DOCKER_IMAGE_CLIENT}
    command: sh -c "npm run build && npm run start"
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
```

### Key CloudFormation Resources

| Resource | Type | Description |
|----------|------|-------------|
| VPC | AWS::EC2::VPC | 10.0.0.0/24 standalone VPC |
| PublicSubnet | AWS::EC2::Subnet | Single AZ public subnet |
| InternetGateway | AWS::EC2::InternetGateway | Internet access |
| EC2Instance | AWS::EC2::Instance | t3.micro instance |
| EC2Role | AWS::IAM::Role | Instance role with ReadOnlyAccess |
| ElasticIP | AWS::EC2::EIP | Static IP address |
