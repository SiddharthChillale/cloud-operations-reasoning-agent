## ADDED Requirements

### Requirement: CDK Stack Provisions Complete Infrastructure
The CDK stack MUST provision all required AWS resources including VPC, ECS Cluster, Aurora Database, S3 Bucket, IAM Roles, and ECR Repository.

#### Scenario: CDK Synthesizes Successfully
- **WHEN** user runs `cdk synth` in the iac/cdk directory
- **THEN** CloudFormation template is generated without errors

#### Scenario: CDK Deploy Creates All Resources
- **WHEN** user runs `cdk deploy --all` with valid AWS credentials
- **THEN** all resources are created in the specified account and region

### Requirement: Configuration via cdk.json
The CDK stack MUST read account ID and region from cdk.json context.

#### Scenario: Context Values Are Used
- **WHEN** cdk.json contains aws_account_id and aws_region
- **THEN** resources are created in the specified account and region

### Requirement: CDK Supports Multiple Environments
The CDK stack MUST support deployment to different environments via context.

#### Scenario: Deploy to Different Account
- **WHEN** user updates cdk.json with different account ID
- **THEN** resources are created in the new account

### Requirement: VPC with Proper Subnet Architecture
The CDK MUST create a VPC with public and private subnets across 3 availability zones.

#### Scenario: VPC Created with 3 AZs
- **WHEN** CDK stack is deployed
- **THEN** VPC is created with 3 public and 3 private subnets across 3 AZs

#### Scenario: Private Subnets Have NAT Access
- **WHEN** VPC is created
- **THEN** NAT Gateways allow private subnet outbound internet access

### Requirement: CloudWatch Container Insights
ECS Cluster MUST have Container Insights enabled for observability.

#### Scenario: Container Insights Enabled
- **WHEN** ECS Cluster is created
- **THEN** Container Insights is enabled in CloudWatch
