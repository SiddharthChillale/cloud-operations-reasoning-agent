## Context

This is a greenfield infrastructure project to create CDK-based IaC for a self-hosted AI agent application. The application consists of a FastAPI backend running smolagents that can interact with AWS resources. Target users are developers who will self-host this in their own AWS accounts.

**Current State:**
- No infrastructure code exists
- Application code exists in `src/` (Python) and `clients/web_ui/nextjs/`
- Uses SQLite with aiosqlite for sessions locally

**Constraints:**
- Self-hosted offering - users deploy in their own AWS accounts
- No ALB, custom domains, Route53, or CI/CD
- Low usage - primarily developers
- Needs CloudWatch dashboard and Container Insights

## Goals / Non-Goals

**Goals:**
- Create CDK TypeScript infrastructure code
- Provision VPC with public/private subnets across 3 AZs
- Deploy ECS Fargate with FastAPI container
- Set up Aurora Serverless v2 PostgreSQL with JSONB
- Create S3 bucket for agent-generated images
- Create IAM role with ReadOnlyPolicy for ECS tasks
- Create ECR repository for Docker images
- Set up CloudWatch dashboard with Container Insights

**Non-Goals:**
- ALB or public-facing load balancer
- Custom domain support with Route53
- CI/CD pipeline
- Application code migration to PostgreSQL (handled separately)
- Multi-region deployment

## Decisions

### 1. CDK over CloudFormation
**Decision:** Use AWS CDK v2 (TypeScript) instead of plain CloudFormation.

**Rationale:**
- More maintainable with TypeScript's type safety
- Easier to create reusable constructs
- Faster development iteration
- Well-suited for self-hosted where users can extend

### 2. ECS Fargate over Lambda/EC2
**Decision:** Use ECS Fargate for compute.

**Rationale:**
- No 15-minute timeout (Lambda limit)
- Serverless - no server management
- Better for long-running AI agent tasks
- smolagents can take time to execute complex operations

### 3. Aurora Serverless v2 over DynamoDB/RDS Provisioned
**Decision:** Use Aurora Serverless v2 with PostgreSQL.

**Rationale:**
- PostgreSQL with JSONB provides SQLite-like flexibility with JSON support
- Serverless - scales to zero when idle, scales up when needed
- Pay-per-use - cost-effective for low usage
- JSONB is faster than plain JSON for querying

### 4. IAM Role with ReadOnlyPolicy
**Decision:** Attach AWS managed ReadOnlyPolicy to ECS task role.

**Rationale:**
- Follows least-privilege principle
- smolagents need read access to AWS resources
- Can extend with inline policies for specific needs

### 5. New VPC with 3 AZs
**Decision:** Create new VPC with 3 availability zones.

**Rationale:**
- High availability for production-like deployments
- Proper isolation between public and private subnets
- NAT Gateways for private subnet outbound access

### 6. Container Insights Enabled
**Decision:** Enable ECS Container Insights.

**Rationale:**
- CloudWatch-based observability
- No additional cost for basic metrics
- Useful for troubleshooting

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Aurora Serverless cold start latency | Acceptable for developer use; set min 1 ACU |
| ECS task role permissions too broad | Start with ReadOnlyPolicy; refine later |
| No ALB means direct container access | Document port 8000 access; users can add ALB |
| CDK version upgrades | Pin CDK version in package.json |
| Self-hosting complexity for users | Provide clear deployment documentation |

## Migration Plan

1. **Bootstrap CDK**: Run `cdk bootstrap` in target account
2. **Deploy Stack**: Run `cdk deploy` to create all resources
3. **Build & Push Image**: User builds Dockerfile, pushes to ECR
4. **Update ECS Service**: Deploy picks up new image
5. **Verify**: Check CloudWatch dashboard, test application

**Rollback:** Run `cdk destroy` to remove all resources.

## Open Questions

- Should the ECS service be public-facing or private? (Defaulting to private with documentation)
- What VPC CIDR to use? (Default 10.0.0.0/16 as discussed)
