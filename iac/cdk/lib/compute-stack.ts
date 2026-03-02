import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface ComputeStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
  readonly vpc: ec2.Vpc;
  readonly clusterSecurityGroup: ec2.SecurityGroup;
  readonly databaseSecret: secretsmanager.Secret;
  readonly databaseSecurityGroup: ec2.SecurityGroup;
  readonly taskExecutionRoleArn: string;
  readonly taskRoleArn: string;
  readonly repository: ecr.Repository;
  readonly imageBucket: s3.Bucket;
}

export class ComputeStack extends cdk.Stack {
  public readonly cluster: ecs.Cluster;
  public readonly service: ecs.FargateService;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const config = props.config;
    const vpc = props.vpc;
    const clusterSecurityGroup = props.clusterSecurityGroup;
    const databaseSecret = props.databaseSecret;
    const databaseSecurityGroup = props.databaseSecurityGroup;
    const taskExecutionRoleArn = props.taskExecutionRoleArn;
    const taskRoleArn = props.taskRoleArn;
    const repository = props.repository;
    const imageBucket = props.imageBucket;

    this.cluster = new ecs.Cluster(this, "CoraECSCluster", {
      clusterName: `cora-cluster-${config.environment}`,
      vpc,
      containerInsights: true,
    });

    const taskExecutionRole = iam.Role.fromRoleArn(
      this,
      "TaskExecutionRole",
      taskExecutionRoleArn,
      { mutable: false }
    );

    const taskRole = iam.Role.fromRoleArn(
      this,
      "TaskRole",
      taskRoleArn,
      { mutable: false }
    );

    imageBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        principals: [taskRole],
        actions: ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        resources: [imageBucket.arnForObjects("*")],
      })
    );

    databaseSecurityGroup.addIngressRule(
      clusterSecurityGroup,
      ec2.Port.tcp(5432),
      "PostgreSQL access from ECS"
    );

    const taskDefinition = new ecs.FargateTaskDefinition(
      this,
      "CoraTaskDefinition",
      {
        cpu: 1024 as any,
        memoryLimitMiB: 2048,
        executionRole: taskExecutionRole,
        taskRole: taskRole,
      }
    );

    const container = taskDefinition.addContainer("cora-api", {
      image: ecs.ContainerImage.fromEcrRepository(repository, "latest"),
      containerName: "cora-api",
      portMappings: [
        {
          containerPort: 8000,
          hostPort: 8000,
          protocol: ecs.Protocol.TCP,
        },
      ],
      environment: {
        AWS_REGION: config.region,
        DATABASE_HOST: "localhost",
        DATABASE_PORT: "5432",
        DATABASE_NAME: "cora",
        S3_BUCKET_NAME: imageBucket.bucketName,
      },
      secrets: {
        DATABASE_USERNAME: ecs.Secret.fromSecretsManager(
          databaseSecret,
          "username"
        ),
        DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(
          databaseSecret,
          "password"
        ),
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "cora-api",
        logRetention: logs.RetentionDays.ONE_WEEK,
      }),
    });

    this.service = new ecs.FargateService(this, "CoraService", {
      serviceName: `cora-api-service-${config.environment}`,
      cluster: this.cluster,
      taskDefinition,
      desiredCount: 1,
      minHealthyPercent: 100,
      maxHealthyPercent: 200,
      securityGroups: [clusterSecurityGroup],
      assignPublicIp: false,
      vpcSubnets: {
        subnets: vpc.privateSubnets,
      },
    });

    new cdk.CfnOutput(this, "ECSClusterName", {
      value: this.cluster.clusterName,
      description: "ECS Cluster Name",
    });

    new cdk.CfnOutput(this, "ECSServiceName", {
      value: this.service.serviceName,
      description: "ECS Service Name",
    });
  }
}
