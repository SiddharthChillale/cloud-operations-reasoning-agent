import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as rds from "aws-cdk-lib/aws-rds";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface DatabaseStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
  readonly vpc: ec2.Vpc;
}

export class DatabaseStack extends cdk.Stack {
  public readonly cluster: rds.DatabaseCluster;
  public readonly secret: secretsmanager.Secret;
  public readonly dbSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const config = props.config;
    const vpc = props.vpc;

    this.secret = new secretsmanager.Secret(this, "CoraDatabaseSecret", {
      secretName: `cora/database-credentials-${config.environment}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          username: "cora_admin",
        }),
        generateStringKey: "password",
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 32,
      },
    });

    this.dbSecurityGroup = new ec2.SecurityGroup(this, "CoraDatabaseSG", {
      vpc,
      securityGroupName: `cora-db-sg-${config.environment}`,
      description: "Security group for Aurora Database",
    });
    this.dbSecurityGroup.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    this.dbSecurityGroup.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(5432),
      "PostgreSQL access from VPC"
    );

    this.cluster = new rds.DatabaseCluster(this, "CoraAuroraCluster", {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_4,
      }),
      clusterIdentifier: `cora-cluster-${config.environment}`,
      credentials: rds.Credentials.fromSecret(this.secret),
      defaultDatabaseName: "cora",
      instanceProps: {
        instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
        vpc,
        vpcSubnets: {
          subnets: vpc.privateSubnets,
        },
      },
      securityGroups: [this.dbSecurityGroup],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new cdk.CfnOutput(this, "DatabaseEndpoint", {
      value: this.cluster.clusterEndpoint.hostname,
      description: "Aurora Database Endpoint",
    });

    new cdk.CfnOutput(this, "DatabaseSecretArn", {
      value: this.secret.secretArn,
      description: "Database Secret ARN",
    });
  }
}
