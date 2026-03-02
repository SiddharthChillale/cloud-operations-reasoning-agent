#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { getConfig } from "../lib/cdk-config";
import { NetworkStack } from "../lib/network-stack";
import { DatabaseStack } from "../lib/database-stack";
import { StorageStack } from "../lib/storage-stack";
import { IamStack } from "../lib/iam-stack";
import { EcrStack } from "../lib/ecr-stack";
import { ComputeStack } from "../lib/compute-stack";
import { ObservabilityStack } from "../lib/observability-stack";

const app = new cdk.App();
const config = getConfig(app);

const networkStack = new NetworkStack(app, "Network", {
  config,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

const storageStack = new StorageStack(app, "Storage", {
  config,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

const iamStack = new IamStack(app, "Iam", {
  config,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

const ecrStack = new EcrStack(app, "Ecr", {
  config,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

const databaseStack = new DatabaseStack(app, "Database", {
  config,
  vpc: networkStack.vpc,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

const computeStack = new ComputeStack(app, "Compute", {
  config,
  vpc: networkStack.vpc,
  clusterSecurityGroup: networkStack.clusterSecurityGroup,
  databaseSecret: databaseStack.secret,
  databaseSecurityGroup: databaseStack.dbSecurityGroup,
  taskExecutionRoleArn: iamStack.taskExecutionRoleArn,
  taskRoleArn: iamStack.taskRoleArn,
  repository: ecrStack.repository,
  imageBucket: storageStack.bucket,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

new ObservabilityStack(app, "Observability", {
  config,
  cluster: computeStack.cluster,
  service: computeStack.service,
  databaseCluster: databaseStack.cluster,
  env: {
    account: config.accountId,
    region: config.region,
  },
});

app.synth();
