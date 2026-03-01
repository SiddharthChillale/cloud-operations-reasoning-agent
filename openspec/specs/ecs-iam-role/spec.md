# ECS IAM Role

## Purpose

IAM roles for ECS task execution and task runtime.

## Requirements

### Requirement: ECS Task Role with ReadOnlyPolicy
The system MUST create an IAM role for ECS tasks with AWS managed ReadOnlyPolicy.

#### Scenario: Task Role Created
- **WHEN** CDK stack is deployed
- **THEN** IAM role for ECS tasks is created

#### Scenario: ReadOnlyPolicy Attached
- **WHEN** Task role is created
- **THEN** AWS ReadOnlyPolicy is attached to the role

### Requirement: S3 Access Policy
ECS task role MUST have inline policy for S3 bucket access.

#### Scenario: S3 Inline Policy
- **WHEN** Task role is configured
- **THEN** inline policy allows s3:GetObject and s3:PutObject on the image bucket

### Requirement: Task Execution Role
ECS task execution role MUST be created for pulling container images.

#### Scenario: Execution Role Created
- **WHEN** CDK stack is deployed
- **THEN** ECS task execution role is created with AmazonECSTaskExecutionRolePolicy

### Requirement: Secrets Manager Access
ECS task role MUST have access to retrieve database credentials from Secrets Manager.

#### Scenario: Secrets Access Policy
- **WHEN** Task role is configured
- **THEN** inline policy allows secretsmanager:GetSecretValue for the database secret
