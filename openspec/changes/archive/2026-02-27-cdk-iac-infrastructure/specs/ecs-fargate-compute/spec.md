## ADDED Requirements

### Requirement: ECS Fargate Service
The system MUST provision an ECS Fargate service to run the FastAPI application.

#### Scenario: ECS Cluster Created
- **WHEN** CDK stack is deployed
- **THEN** ECS Fargate cluster is created with Container Insights enabled

#### Scenario: ECS Service Running
- **WHEN** ECS cluster is created
- **THEN** ECS service is created with desired count of 1

### Requirement: Task Definition Configuration
ECS task definition MUST have appropriate CPU and memory settings.

#### Scenario: Task CPU Configuration
- **WHEN** Task definition is created
- **THEN** CPU is set to 1024 (1 vCPU)

#### Scenario: Task Memory Configuration
- **WHEN** Task definition is created
- **THEN** Memory is set to 2048 (2 GiB)

### Requirement: Container Port Configuration
ECS container MUST expose port 8000 for FastAPI.

#### Scenario: Container Port Mapping
- **WHEN** Container is configured
- **THEN** Port 8000 is exposed and mapped to host port 8000

### Requirement: Task Role with IAM Permissions
ECS task MUST have an IAM role with ReadOnlyPolicy for AWS resource access.

#### Scenario: Task Role Attached
- **WHEN** ECS task runs
- **THEN** task role has AWS ReadOnlyPolicy attached

### Requirement: Security Group Configuration
ECS tasks MUST have a security group allowing access to port 8000.

#### Scenario: Security Group Allows Access
- **WHEN** Security group is created
- **THEN** Port 8000 is accessible from within the VPC
