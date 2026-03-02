# CORA POC Infrastructure

Lightweight CloudFormation setup for running CORA on a single EC2 instance with Cloudflare Tunnel for browser access.

## Architecture

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

## Files

| File | Description |
|------|-------------|
| `poc-template.yaml` | CloudFormation template (full stack) |
| `docker-compose.yml` | Docker Compose for FastAPI + Next.js |
| `user-data.sh` | Standalone user data script (manual EC2) |

## Quick Start

### Option 1: Deploy with CloudFormation

1. **Prerequisites:**
   - Docker images pushed to Docker Hub
   - Cloudflare account with Zero Trust
   - Google Cloud project for OAuth

2. **Configure Cloudflare:**
   - Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com)
   - Create a tunnel → copy the token
   - Go to Access → Applications → Add Self-hosted app
   - Configure domain: `*.trycloudflare.com`
   - Add Google login: Settings → Authentication → Add Google

3. **Configure Google OAuth:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create project → APIs & Services → Credentials
   - Configure OAuth consent screen (External)
   - Create OAuth client ID (Web app)
   - Authorized redirect: `https://<your-team>.cloudflareaccess.com/cdn-cgi/access/callback`

4. **Deploy CloudFormation:**
   ```bash
   # Update AMI ID for your region if needed
   # The template uses us-east-1 Amazon Linux 2023 AMI
   
   aws cloudformation deploy \
     --template-file poc-template.yaml \
     --stack-name cora-poc \
     --parameter-overrides \
       AccountId=123456789012 \
       DockerImageApi=youruser/cora:latest \
       DockerImageClient=youruser/cora-client:latest \
       CloudflareToken=your-cloudflare-token \
       GoogleClientId=your-google-client-id \
       GoogleClientSecret=your-google-client-secret \
       KeyPairName=your-key-pair
   ```

5. **Get the URL:**
   ```bash
   # SSH to EC2 and check tunnel logs
   ssh -i your-key.pem ec2-user@<elastic-ip>
   cat /var/log/cloudflared.log
   ```

### Option 2: Manual EC2 Launch

1. Launch an EC2 instance (Amazon Linux 2023, t3.micro)
2. Paste `user-data.sh` into user data (base64 encoded)
3. Or SSH in and run the script manually:
   ```bash
   curl -sL https://raw/main/iac/cloudformation/user-data.sh | \
     DOCKER_IMAGE_API=youruser/cora:latest \
     DOCKER_IMAGE_CLIENT=youruser/cora-client:latest \
     CLOUDFLARE_TOKEN=your-token \
     AWS_ROLE_ARN=arn:aws:iam::123456789012:role/YourRoleName \
     bash
   ```

## Cross-Account Access

If you want EC2 in Account 1 to access resources in Account 2:

### Step 1: Configure Role in Account 2 (Demo Account)

1. Go to IAM → Roles → Select your existing role
2. Edit **Trust Policy** (Trust relationships tab):
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
   Replace `ACCOUNT1` with your Account 1 number.

3. Ensure the role has `ReadOnlyAccess` policy

### Step 2: Deploy with Cross-Account Role

```bash
aws cloudformation deploy \
  --template-file poc-template.yaml \
  --stack-name cora-poc \
  --parameter-overrides \
    AccountId=123456789012 \
    DockerImageApi=youruser/cora:latest \
    DockerImageClient=youruser/cora-client:latest \
    CloudflareToken=your-cloudflare-token \
    CrossAccountRoleArn=arn:aws:iam::ACCOUNT2:role/YourRoleName
```

The EC2 will automatically assume the cross-account role when making AWS API calls. No `--profile` flag needed - just set `AWS_ROLE_ARN`.

## Operations

### Start (Bring up)
```bash
# Via CloudFormation
aws cloudformation update-stack --stack-name cora-poc ... 

# Or just start the EC2
aws ec2 start-instances --instance-id <instance-id>
```

### Stop (Bring down)
```bash
# Stop EC2 (data persists on EBS)
aws ec2 stop-instances --instance-id <instance-id>
```

### Destroy (Delete everything)
```bash
# Delete CloudFormation stack (all resources gone)
aws cloudformation delete-stack --stack-name cora-poc
```

## CloudWatch Logs

Logs are automatically shipped to CloudWatch:
- Log Group: `/aws/ec2/cora-poc`
- Retention: 7 days
- Streams: `{instance_id}/setup`, `{instance_id}/cloudflared`

View logs:
```bash
aws logs tail /aws/ec2/cora-poc --follow
```

## Security

- **IAM Role**: Instance has `ReadOnlyAccess` on all AWS resources
- **Access Control**: Cloudflare Zero Trust with Google authentication
- **Policy**: Restrict to `@yourcompany.com` or `@gmail.com`

## Cost

| Resource | Cost (us-east-1) |
|----------|------------------|
| EC2 t3.micro | ~$8/month |
| EBS (8GB) | ~$1/month |
| Data transfer | ~$1/month |
| **Total** | **~$10/month** |

## Troubleshooting

### Services not starting
```bash
# Check Docker status
docker ps
docker logs cora-api
docker logs cora-client

# Check docker-compose
cd /opt/cora
docker-compose logs
```

### Cloudflare tunnel not working
```bash
# Check tunnel logs
cat /var/log/cloudflared.log

# Restart tunnel
pkill cloudflared
nohup cloudflared tunnel --url http://localhost:3000 --token "$CLOUDFLARE_TOKEN" > /var/log/cloudflared.log 2>&1 &
```

### Can't access URL
1. Check Cloudflare Access Policy allows your email
2. Verify tunnel is running: `ps aux | grep cloudflared`
3. Check Security Group allows outbound 443
