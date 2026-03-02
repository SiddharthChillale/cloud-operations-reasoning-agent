## Why

This project requires cloud infrastructure to deploy a self-hosted AI agent application (smolagents with FastAPI backend) for developers. Currently, there is no Infrastructure as Code (IaC) setup, making deployment to AWS manual and error-prone. The application needs compute (ECS Fargate), database (Aurora Serverless PostgreSQL), storage (S3), and IAM roles with ReadOnlyPolicy for AWS operations.

## What Changes

- Create CDK-based IaC in TypeScript under `iac/cdk/`
- Set up new VPC with public/private subnets across 3 AZs
- Deploy ECS Fargate cluster with FastAPI container
- Provision Aurora Serverless v2 PostgreSQL with JSONB support
- Create S3 bucket for agent-generated images
- Create IAM role with AWS ReadOnlyPolicy for ECS task execution
- Create ECR repository for Docker image storage
- Set up CloudWatch dashboard with Container Insights
- Create Dockerfile for the FastAPI application

## Capabilities

### New Capabilities

- **cdk-infrastructure**: CDK stack that provisions all AWS resources (VPC, ECS, Aurora, S3, IAM, CloudWatch)
- **aurora-postgresql-database**: Aurora Serverless v2 PostgreSQL with JSONB support for session storage
- **ecs-fargate-compute**: ECS Fargate service running FastAPI with smolagents
- **s3-image-storage**: S3 bucket for storing agent-generated images
- **ecs-iam-role**: IAM role with ReadOnlyPolicy attached to ECS tasks for AWS API access

### Modified Capabilities

- (None - new infrastructure)

## Impact

- New directory: `iac/cdk/` with TypeScript CDK code
- New file: `Dockerfile` for containerizing the FastAPI application
- Affected systems: AWS (ECS, Aurora, S3, IAM, CloudWatch, ECR)
