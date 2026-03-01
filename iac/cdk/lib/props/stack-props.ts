import * as cdk from "aws-cdk-lib";
import { CdkConfig } from "../cdk-config";

export interface CoraStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
}
