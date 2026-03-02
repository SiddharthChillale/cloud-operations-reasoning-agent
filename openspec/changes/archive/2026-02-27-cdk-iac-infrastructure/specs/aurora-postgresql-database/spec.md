## ADDED Requirements

### Requirement: Aurora Serverless v2 PostgreSQL
The system MUST provision Aurora Serverless v2 with PostgreSQL engine for session storage.

#### Scenario: Aurora Cluster Created
- **WHEN** CDK stack is deployed
- **THEN** Aurora Serverless v2 cluster is created with PostgreSQL engine

#### Scenario: Serverless Scaling Configuration
- **WHEN** Aurora cluster is created
- **THEN** min capacity is 1 ACU and max capacity is 2 ACU

### Requirement: Database Schema for Sessions
The database MUST support sessions, messages, and agent run metrics tables with JSONB support.

#### Scenario: Sessions Table Exists
- **WHEN** Database is initialized
- **THEN** sessions table exists with columns: id, title, status, created_at, updated_at, is_active, agent_steps

#### Scenario: Messages Table Exists
- **WHEN** Database is initialized
- **THEN** messages table exists with columns: id, session_id, role, content, timestamp

#### Scenario: Agent Metrics Table Exists
- **WHEN** Database is initialized
- **THEN** agent_run_metrics table exists with columns: session_id, run_number, step_number, step_type, input_tokens, output_tokens, total_tokens

### Requirement: Secrets Manager Integration
Database credentials MUST be stored in Secrets Manager.

#### Scenario: Credentials Stored Securely
- **WHEN** Aurora cluster is created
- **THEN** database credentials are stored in Secrets Manager

### Requirement: Security Group Configuration
The database MUST have a security group allowing access from ECS tasks.

#### Scenario: Security Group Allows PostgreSQL
- **WHEN** Security group is created
- **THEN** PostgreSQL port 5432 is accessible from ECS security group
