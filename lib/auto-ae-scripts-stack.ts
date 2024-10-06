import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";

export class AutoAeScriptsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Update world

    const updateWorld = new lambda.DockerImageFunction(this, "updateWorld", {
      code: lambda.DockerImageCode.fromImageAsset("./image", {
        file: "Dockerfile-update-world",
      }),
      memorySize: 128,
      timeout: cdk.Duration.seconds(5),
      architecture: lambda.Architecture.ARM_64,
    });

    const updateWorldUrl = updateWorld.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
        allowedOrigins: ["*"],
      },
    });

    new cdk.CfnOutput(this, "updateWorldUrl", {
      value: updateWorldUrl.url,
    });

    // Update session token

    const updateSessionToken = new lambda.DockerImageFunction(
      this,
      "updateSessionToken",
      {
        code: lambda.DockerImageCode.fromImageAsset("./image", {
          file: "Dockerfile-update-session-token",
        }),
        memorySize: 128,
        timeout: cdk.Duration.seconds(5),
        architecture: lambda.Architecture.ARM_64,
      }
    );

    const updateSessionTokenUrl = updateSessionToken.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
        allowedOrigins: ["*"],
      },
    });

    new cdk.CfnOutput(this, "updateSessionTokenUrl", {
      value: updateSessionTokenUrl.url,
    });

    // Update aircraft

    const updateAircraft = new lambda.DockerImageFunction(
      this,
      "updateAircraft",
      {
        code: lambda.DockerImageCode.fromImageAsset("./image", {
          file: "Dockerfile-update-aircraft",
        }),
        memorySize: 128,
        timeout: cdk.Duration.seconds(5),
        architecture: lambda.Architecture.ARM_64,
      }
    );

    const updateAircraftUrl = updateAircraft.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
        allowedOrigins: ["*"],
      },
    });

    new cdk.CfnOutput(this, "updateAircraftUrl", {
      value: updateAircraftUrl.url,
    });

    // Run config

    const runConfiguration = new lambda.DockerImageFunction(
      this,
      "runConfiguration",
      {
        code: lambda.DockerImageCode.fromImageAsset("./image", {
          file: "Dockerfile-run-configuration",
        }),
        memorySize: 256,
        timeout: cdk.Duration.seconds(20),
        architecture: lambda.Architecture.ARM_64,
      }
    );

    const runConfigurationUrl = runConfiguration.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
        allowedOrigins: ["*"],
      },
    });

    new cdk.CfnOutput(this, "runConfigurationUrl", {
      value: runConfigurationUrl.url,
    });
  }
}
