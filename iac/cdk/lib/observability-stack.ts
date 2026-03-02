import * as cdk from "aws-cdk-lib";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as rds from "aws-cdk-lib/aws-rds";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import { Construct } from "constructs";
import { CdkConfig } from "./cdk-config";

export interface ObservabilityStackProps extends cdk.StackProps {
  readonly config: CdkConfig;
  readonly cluster: ecs.Cluster;
  readonly service: ecs.FargateService;
  readonly databaseCluster: rds.DatabaseCluster;
}

export class ObservabilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ObservabilityStackProps) {
    super(scope, id, props);

    const config = props.config;
    const cluster = props.cluster;
    const service = props.service;
    const databaseCluster = props.databaseCluster;

    const dashboard = new cloudwatch.Dashboard(this, "CoraDashboard", {
      dashboardName: `cora-dashboard-${config.environment}`,
    });

    const ecsMetric = new cloudwatch.Metric({
      namespace: "AWS/ECS",
      metricName: "CPUUtilization",
      dimensionsMap: {
        ClusterName: cluster.clusterName,
        ServiceName: service.serviceName,
      },
      statistic: "Average",
      period: cdk.Duration.minutes(5),
    });

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "ECS CPU Utilization",
        left: [ecsMetric],
        width: 12,
      })
    );

    const rdsMetric = new cloudwatch.Metric({
      namespace: "AWS/RDS",
      metricName: "CPUUtilization",
      dimensionsMap: {
        DBClusterIdentifier: databaseCluster.clusterIdentifier,
      },
      statistic: "Average",
      period: cdk.Duration.minutes(5),
    });

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Aurora CPU Utilization",
        left: [rdsMetric],
        width: 12,
      })
    );

    const rdsConnections = new cloudwatch.Metric({
      namespace: "AWS/RDS",
      metricName: "DatabaseConnections",
      dimensionsMap: {
        DBClusterIdentifier: databaseCluster.clusterIdentifier,
      },
      statistic: "Sum",
      period: cdk.Duration.minutes(5),
    });

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Aurora Database Connections",
        left: [rdsConnections],
        width: 12,
      })
    );

    dashboard.addWidgets(
      new cloudwatch.SingleValueWidget({
        title: "Estimated Monthly Cost (ECS)",
        metrics: [
          new cloudwatch.Metric({
            namespace: "AWS/Billing",
            metricName: "EstimatedCharges",
            dimensionsMap: {
              ServiceName: "AmazonECS",
            },
            statistic: "Maximum",
          }),
        ],
        width: 6,
      })
    );

    new cdk.CfnOutput(this, "DashboardName", {
      value: dashboard.dashboardName,
      description: "CloudWatch Dashboard Name",
    });
  }
}
