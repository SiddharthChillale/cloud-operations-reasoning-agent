## 1. CDK Project Setup

- [x] 1.1 Create iac/cdk/ directory structure (bin/, lib/, test/)
- [x] 1.2 Create cdk.json with account ID and region configuration
- [x] 1.3 Create package.json with AWS CDK v2, TypeScript dependencies
- [x] 1.4 Create tsconfig.json for TypeScript configuration
- [x] 1.5 Initialize npm and install dependencies

## 2. CDK Core Infrastructure

- [x] 2.1 Create lib/cdk-config.ts for configuration helpers
- [x] 2.2 Create lib/props/stack-props.ts for TypeScript interfaces
- [x] 2.3 Create bin/cdk.ts as CDK app entry point
- [x] 2.4 Create lib/cdk-stack.ts as main CloudFormation stack

## 3. VPC and Networking

- [x] 3.1 Create VPC with 10.0.0.0/16 CIDR block
- [x] 3.2 Create public subnets in 3 availability zones
- [x] 3.3 Create private subnets in 3 availability zones
- [x] 3.4 Create Internet Gateway and attach to VPC
- [x] 3.5 Create NAT Gateways in public subnets
- [x] 3.6 Configure route tables for public and private subnets
- [x] 3.7 Create VPC endpoints for ECR, S3, Secrets Manager

## 4. Aurora Database

- [x] 4.1 Create Aurora PostgreSQL cluster
- [x] 4.2 Configure instance (using t3.micro for cost efficiency)
- [x] 4.3 Set up database name (cora) and credentials via Secrets Manager
- [x] 4.4 Create security group for PostgreSQL access
- [x] 4.5 Configure VPC subnet group for Aurora

## 5. ECS Fargate Compute

- [x] 5.1 Create ECS cluster with Container Insights enabled
- [x] 5.2 Create ECS task definition with 1 vCPU and 2 GiB memory
- [x] 5.3 Configure container port 8000 for FastAPI
- [x] 5.4 Create ECS service with desired count 1
- [x] 5.5 Create security group for ECS tasks (port 8000)

## 6. IAM Roles and Permissions

- [x] 6.1 Create ECS task execution role with AmazonECSTaskExecutionRolePolicy
- [x] 6.2 Create ECS task role with AWS ReadOnlyPolicy
- [x] 6.3 Add inline policy for S3 bucket access to task role
- [x] 6.4 Add inline policy for Secrets Manager access to task role
- [x] 6.5 Attach IAM roles to ECS task definition

## 7. S3 Image Storage

- [x] 7.1 Create S3 bucket with unique name (account-region)
- [x] 7.2 Block public access on S3 bucket
- [x] 7.3 Enable S3 versioning
- [x] 7.4 Create bucket policy for ECS task role access

## 8. ECR Repository

- [x] 8.1 Create ECR repository for FastAPI image
- [x] 8.2 Enable image scanning on push
- [x] 8.3 Add lifecycle policy for old images

## 9. CloudWatch Dashboard

- [x] 9.1 Create CloudWatch dashboard
- [x] 9.2 Add ECS cluster metrics widget
- [x] 9.3 Add Aurora database metrics widget
- [x] 9.4 Add S3 bucket metrics widget
- [x] 9.5 Add estimated cost widget

## 10. Dockerfile

- [x] 10.1 Create Dockerfile in project root
- [x] 10.2 Set up multi-stage build (builder + runtime)
- [x] 10.3 Install Python 3.12 and uv
- [x] 10.4 Copy application dependencies
- [x] 10.5 Expose port 8000
- [x] 10.6 Configure uvicorn as entrypoint

## 11. Verification

- [x] 11.1 Run cdk synth to validate CloudFormation template
- [ ] 11.2 Run cdk bootstrap in target AWS account
- [ ] 11.3 Run cdk deploy --all to create resources
- [ ] 11.4 Verify ECS service is running
- [ ] 11.5 Verify Aurora cluster is available
- [ ] 11.6 Verify CloudWatch dashboard is accessible
- [ ] 11.7 Document deployment steps for end users
