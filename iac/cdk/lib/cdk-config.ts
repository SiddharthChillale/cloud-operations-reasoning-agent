import * as cdk from "aws-cdk-lib";

export interface CdkConfig {
  readonly accountId: string;
  readonly region: string;
  readonly environment: string;
}

export function getConfig(scope: cdk.App): CdkConfig {
  const accountId = scope.node.tryGetContext("aws_account_id") as string;
  const region = scope.node.tryGetContext("aws_region") as string;
  const environment = scope.node.tryGetContext("environment") as string;

  if (!accountId || !region) {
    throw new Error(
      "aws_account_id and aws_region must be defined in cdk.json context"
    );
  }

  return {
    accountId,
    region,
    environment: environment || "dev",
  };
}
