import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface StorageStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
}

export class StorageStack extends cdk.Stack {
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: StorageStackProps) {
    super(scope, id, props);

    const config = props.config;

    this.bucket = new s3.Bucket(this, "CoraImageBucket", {
      bucketName: `cora-agent-images-${config.accountId}-${config.region}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new cdk.CfnOutput(this, "S3BucketName", {
      value: this.bucket.bucketName,
      description: "S3 Bucket for Agent Images",
    });
  }
}
