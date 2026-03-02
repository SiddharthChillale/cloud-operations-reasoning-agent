import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface IamStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
}

export class IamStack extends cdk.Stack {
  public readonly taskExecutionRole: iam.Role;
  public readonly taskRole: iam.Role;
  public readonly taskExecutionRoleArn: string;
  public readonly taskRoleArn: string;

  constructor(scope: Construct, id: string, props: IamStackProps) {
    super(scope, id, props);

    const config = props.config;

    this.taskExecutionRole = new iam.Role(
      this,
      "CoraTaskExecutionRole",
      {
        roleName: `cora-task-execution-role-${config.environment}`,
        assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName(
            "AmazonECSTaskExecutionRolePolicy"
          ),
        ],
      }
    );

    this.taskRole = new iam.Role(this, "CoraTaskRole", {
      roleName: `cora-task-role-${config.environment}`,
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });

    this.taskRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName("ReadOnlyAccess")
    );

    const secretsAccessPolicy = new iam.Policy(this, "SecretsAccessPolicy", {
      policyName: `cora-secrets-access-${config.environment}`,
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["secretsmanager:GetSecretValue"],
          resources: ["*"],
        }),
      ],
    });
    this.taskRole.attachInlinePolicy(secretsAccessPolicy);

    this.taskExecutionRoleArn = this.taskExecutionRole.roleArn;
    this.taskRoleArn = this.taskRole.roleArn;

    new cdk.CfnOutput(this, "TaskExecutionRoleArn", {
      value: this.taskExecutionRoleArn,
      description: "ECS Task Execution Role ARN",
    });

    new cdk.CfnOutput(this, "TaskRoleArn", {
      value: this.taskRoleArn,
      description: "ECS Task Role ARN",
    });
  }
}
