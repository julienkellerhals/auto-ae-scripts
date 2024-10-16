import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dotenv from "dotenv";

export class AutoAeScriptsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    dotenv.config();

    // Update world

    const updateWorld = new lambda.DockerImageFunction(this, "updateWorld", {
      code: lambda.DockerImageCode.fromImageAsset("./image", {
        file: "Dockerfile-update-world",
      }),
      memorySize: 128,
      timeout: cdk.Duration.seconds(10),
      architecture: lambda.Architecture.ARM_64,
      environment: {
        DB_USERNAME: process.env.DB_USERNAME || "",
        DB_PASSWORD: process.env.DB_PASSWORD || "",
        DB_URL: process.env.DB_URL || "",
        DATABASE: process.env.DATABASE || "",
      },
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
        environment: {
          DB_USERNAME: process.env.DB_USERNAME || "",
          DB_PASSWORD: process.env.DB_PASSWORD || "",
          DB_URL: process.env.DB_URL || "",
          DATABASE: process.env.DATABASE || "",
        },
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
        timeout: cdk.Duration.seconds(20),
        architecture: lambda.Architecture.ARM_64,
        environment: {
          DB_USERNAME: process.env.DB_USERNAME || "",
          DB_PASSWORD: process.env.DB_PASSWORD || "",
          DB_URL: process.env.DB_URL || "",
          DATABASE: process.env.DATABASE || "",
        },
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

    // Update flights

    const updateFlights = new lambda.DockerImageFunction(
      this,
      "updateFlights",
      {
        code: lambda.DockerImageCode.fromImageAsset("./image", {
          file: "Dockerfile-update-flights",
        }),
        memorySize: 128,
        timeout: cdk.Duration.seconds(120),
        architecture: lambda.Architecture.ARM_64,
        environment: {
          DB_USERNAME: process.env.DB_USERNAME || "",
          DB_PASSWORD: process.env.DB_PASSWORD || "",
          DB_URL: process.env.DB_URL || "",
          DATABASE: process.env.DATABASE || "",
        },
      }
    );

    const updateFlightsUrl = updateFlights.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
        allowedOrigins: ["*"],
      },
    });

    new cdk.CfnOutput(this, "updateFlightsUrl", {
      value: updateFlightsUrl.url,
    });

    // Run config

    const runConfiguration = new lambda.DockerImageFunction(
      this,
      "runConfiguration",
      {
        code: lambda.DockerImageCode.fromImageAsset("./image", {
          file: "Dockerfile-run-configuration",
        }),
        memorySize: 128,
        timeout: cdk.Duration.seconds(120),
        architecture: lambda.Architecture.ARM_64,
        environment: {
          DB_USERNAME: process.env.DB_USERNAME || "",
          DB_PASSWORD: process.env.DB_PASSWORD || "",
          DB_URL: process.env.DB_URL || "",
          DATABASE: process.env.DATABASE || "",
        },
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
