# [WIP] THIS HAS NOT BEEN TESTED.

# CORA CDK Infrastructure

AWS CloudFormation Infrastructure as Code for deploying the CORA (AI Agent Platform) using AWS CDK v2 with TypeScript.

## Overview

This CDK project provisions a complete AWS infrastructure for self-hosting the CORA application:

- **Compute**: ECS Fargate (1 vCPU, 2 GiB)
- **Database**: Aurora PostgreSQL (t3.micro)
- **Storage**: S3 bucket for agent-generated images
- **IAM**: Roles with ReadOnlyPolicy for ECS tasks
- **Observability**: CloudWatch dashboard with Container Insights

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              VPC (10.0.0.0/16)                       │
│                                                                       │
│  ┌─────────────────────────┐    ┌────────────────────────────────┐ │
│  │    Public Subnets      │    │       Private Subnets           │ │
│  │    (AZ1, AZ2, AZ3)     │    │       (AZ1, AZ2, AZ3)           │ │
│  │                        │    │                                 │ │
│  │  ┌──────────────────┐  │    │  ┌──────────────────────────┐   │ │
│  │  │  NAT Gateway     │  │    │  │   ECS Fargate Tasks     │   │ │
│  │  └──────────────────┘  │    │  └──────────────────────────┘   │ │
│  └─────────────────────────┘    └────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                Aurora PostgreSQL (t3.micro)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Bucket    │    │   ECR Repo      │    │  CloudWatch     │
│  (images)      │    │  (Docker img)   │    │  Dashboard      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Stack Structure

| Stack | File | Description |
|-------|------|-------------|
| NetworkStack | `network-stack.ts` | VPC, subnets, NAT GWs, security groups, endpoints |
| DatabaseStack | `database-stack.ts` | Aurora PostgreSQL, Secrets Manager |
| StorageStack | `storage-stack.ts` | S3 bucket for agent images |
| IamStack | `iam-stack.ts` | ECS task execution and task roles |
| EcrStack | `ecr-stack.ts` | ECR repository for Docker image |
| ComputeStack | `compute-stack.ts` | ECS Fargate cluster and service |
| ObservabilityStack | `observability-stack.ts` | CloudWatch dashboard |

### Stack Dependencies

```
NetworkStack
    ├──→ DatabaseStack
    ├──→ StorageStack
    ├──→ IamStack
    ├──→ EcrStack
    └──→ ComputeStack (depends on all above)
              └──→ ObservabilityStack
```

## Prerequisites

1. **AWS Account**: An AWS account with appropriate permissions
2. **AWS CLI**: Configured with credentials
3. **Node.js**: 18.x or later
4. **npm**: Comes with Node.js
5. **AWS CDK v2**: Installed globally or use `npx`

## Installation

```bash
cd iac/cdk
npm install
```

## Configuration

Edit `cdk.json` to configure your AWS account and region:

```json
{
  "app": "npx ts-node bin/cdk.ts",
  "context": {
    "aws_account_id": "123456789012",
    "aws_region": "us-east-2",
    "environment": "dev"
  }
}
```

### Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `aws_account_id` | AWS Account ID | Required |
| `aws_region` | AWS Region | Required |
| `environment` | Environment name (dev, prod, etc.) | `dev` |

## Deployment

### 1. Bootstrap CDK (first time only)

```bash
cd iac/cdk
cdk bootstrap aws://{account-id}/{region}
```

### 2. Synthesize CloudFormation template

```bash
cdk synth
```

This validates the CDK code and outputs the CloudFormation template.

### 3. Deploy all stacks

```bash
cdk deploy --all
```

### 4. Deploy specific stacks

```bash
# Deploy only network and database
cdk deploy NetworkStack DatabaseStack

# Deploy compute only (if others exist)
cdk deploy ComputeStack
```

## Post-Deployment

### 1. Build and push Docker image

After deployment, you need to build and push the Docker image to ECR:

```bash
# Get ECR repository URI from stack outputs
aws cloudformation describe-stacks --stack-name Ecr --region {region} \
  --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryUri'].OutputValue" \
  --output text

# Login to ECR
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account-id}.dkr.ecr.{region}.amazonaws.com

# Build and push
docker build -t cora-api:latest .
docker tag cora-api:latest {account-id}.dkr.ecr.{region}.amazonaws.com/cora-api-{env}:latest
docker push {account-id}.dkr.ecr.{region}.amazonaws.com/cora-api-{env}:latest
```

### 2. Access the application

The ECS service runs in private subnets. To access it:

- **Option A**: Use ECS Exec or SSM Session Manager
- **Option B**: Add an Application Load Balancer (not included - see Future Enhancements)
- **Option C**: VPN/Direct Connect to VPC

### 3. Get service endpoint

```bash
aws ecs describe-services --cluster cora-cluster-{env} \
  --services cora-api-service-{env} --region {region}
```

## Cleanup / Destroy

To completely remove all resources and return to a clean state:

```bash
cdk destroy --all
```

### What Gets Deleted

| Resource | Behavior |
|----------|----------|
| VPC | ✓ Deleted |
| Subnets | ✓ Deleted |
| NAT Gateways | ✓ Deleted |
| Security Groups | ✓ Deleted |
| Aurora DB | ✓ Deleted (no snapshot) |
| Secrets Manager | ✓ Deleted |
| S3 Bucket | ✓ Deleted (all objects) |
| ECR Images | ✓ Deleted |
| CloudWatch Logs | Auto-delete after 7 days |
| IAM Roles | ✓ Deleted |

### Important Notes

- **S3 Bucket**: All objects are deleted when the bucket is deleted
- **ECR Repository**: All images are deleted before repository deletion
- **CloudWatch Logs**: Logs are retained for 7 days then auto-deleted
- **Aurora DB**: Database is deleted without creating a final snapshot

## Cost Considerations

This infrastructure uses the following AWS resources that incur costs:

| Service | Configuration | Estimated Cost (us-east-2) |
|---------|--------------|---------------------------|
| VPC | 3 AZs NAT GWs | ~$100/month |
| Aurora PostgreSQL | t3.micro | ~$30/month (always-on) |
| ECS Fargate | 1 vCPU, 2 GiB | ~$25/month |
| S3 | Storage + requests | ~$1/month |
| ECR | Storage | ~$1/month |
| CloudWatch | Basic metrics | ~$10/month |
| **Total** | | **~$167/month** |

### Cost Optimization Tips

1. **Aurora Serverless v2**: Consider upgrading to Aurora Serverless v2 for pay-per-use (currently uses provisioned t3.micro)
2. **ECS Scheduling**: Use scheduled scaling to scale to zero when not in use
3. **NAT Gateway**: Consider NAT Instance for development (lower cost but less reliable)

## Environment Variables for Container

The ECS container receives these environment variables:

| Variable | Description |
|----------|-------------|
| `AWS_REGION` | AWS region from config |
| `DATABASE_HOST` | Aurora cluster endpoint |
| `DATABASE_PORT` | 5432 (PostgreSQL) |
| `DATABASE_NAME` | cora |
| `S3_BUCKET_NAME` | Agent images bucket name |

Secrets (from Secrets Manager):
- `DATABASE_USERNAME`
- `DATABASE_PASSWORD`

## Security Considerations

### IAM Roles

- **Task Execution Role**: Has `AmazonECSTaskExecutionRolePolicy` (pulls images, writes to CloudWatch)
- **Task Role**: Has `ReadOnlyAccess` + Secrets Manager access

### Security Groups

- **Cluster SG**: Allows port 8000 from VPC
- **Database SG**: Allows port 5432 from Cluster SG only

### Network

- ECS tasks run in **private subnets** with no public IP
- Access requires VPC connectivity (VPN, ALB, or bastion)

## Future Enhancements

The following are NOT included but can be added:

1. **Application Load Balancer** - For public HTTP access
2. **ACM Certificate** - For HTTPS
3. **Route53 DNS** - For custom domains
4. **Aurora Serverless v2** - For pay-per-use database
5. **Auto Scaling** - Based on CPU/memory metrics
6. **VPN/PrivateLink** - For secure access
7. **WAF** - For DDoS protection

## Troubleshooting

### ECS service not starting

Check task definition and logs:
```bash
aws ecs describe-tasks --cluster cora-cluster-{env} --tasks {task-id} --region {region}
aws logs get-log-events --log-group-name /ecs/cora-api --log-stream-name {stream}
```

### Cannot connect to database

Check security groups and database status:
```bash
aws rds describe-db-instances --db-instance-identifier cora-cluster-{env} --region {region}
```

### CDK deployment fails

Ensure you have proper IAM permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

## File Structure

```
iac/cdk/
├── bin/
│   └── cdk.ts                 # CDK app entry point
├── lib/
│   ├── cdk-config.ts          # Configuration helpers
│   ├── network-stack.ts        # VPC and networking
│   ├── database-stack.ts      # Aurora PostgreSQL
│   ├── storage-stack.ts       # S3 bucket
│   ├── iam-stack.ts          # IAM roles
│   ├── ecr-stack.ts          # ECR repository
│   ├── compute-stack.ts       # ECS Fargate
│   └── observability-stack.ts # CloudWatch dashboard
├── test/                      # Test files (when added)
├── cdk.json                   # CDK configuration
├── package.json               # Node dependencies
└── tsconfig.json              # TypeScript config
```

## License

MIT
