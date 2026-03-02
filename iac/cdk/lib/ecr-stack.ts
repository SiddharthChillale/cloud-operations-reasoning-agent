import * as cdk from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface EcrStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
}

export class EcrStack extends cdk.Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, props: EcrStackProps) {
    super(scope, id, props);

    const config = props.config;

    this.repository = new ecr.Repository(this, "CoraECRRepository", {
      repositoryName: `cora-api-${config.environment}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
      imageScanOnPush: true,
      lifecycleRules: [
        {
          description: "Remove old images",
          maxImageCount: 10,
        },
      ],
    });

    new cdk.CfnOutput(this, "ECRRepositoryUri", {
      value: this.repository.repositoryUri,
      description: "ECR Repository URI",
    });
  }
}
