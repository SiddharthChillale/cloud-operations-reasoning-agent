import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface NetworkStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
}

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  public readonly vpcId: string;
  public readonly privateSubnets: ec2.ISubnet[];
  public readonly clusterSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    const config = props.config;

    this.vpc = new ec2.Vpc(this, "CoraVPC", {
      vpcName: `cora-vpc-${config.environment}`,
      ipAddresses: ec2.IpAddresses.cidr("10.0.0.0/16"),
      maxAzs: 3,
      natGateways: 3,
      enableDnsHostnames: true,
      enableDnsSupport: true,
      subnetConfiguration: [
        {
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });
    this.vpc.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    this.vpcId = this.vpc.vpcId;
    this.privateSubnets = this.vpc.privateSubnets;

    this.vpc.addInterfaceEndpoint("ECREndpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.ECR,
      subnets: { subnets: this.vpc.privateSubnets },
    });

    this.vpc.addInterfaceEndpoint("SecretsManagerEndpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      subnets: { subnets: this.vpc.privateSubnets },
    });

    this.vpc.addGatewayEndpoint("S3Endpoint", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });

    this.clusterSecurityGroup = new ec2.SecurityGroup(
      this,
      "CoraClusterSG",
      {
        vpc: this.vpc,
        securityGroupName: `cora-cluster-sg-${config.environment}`,
        description: "Security group for ECS Cluster",
      }
    );
    this.clusterSecurityGroup.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    new cdk.CfnOutput(this, "VPCId", {
      value: this.vpcId,
      description: "VPC ID",
    });

    new cdk.CfnOutput(this, "PrivateSubnetIds", {
      value: this.vpc.privateSubnets.map((s) => s.subnetId).join(","),
      description: "Private Subnet IDs",
    });
  }
}
