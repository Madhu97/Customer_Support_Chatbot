import json
import os
import time

import boto3


REGION = "us-east-1"
STACK_NAME = "bug-report-tool-stack"

GATEWAY_NAME = "bug-report-gateway"
TARGET_NAME = "bugreports"


def get_stack_outputs():
    cf = boto3.client(
        "cloudformation",
        region_name=REGION
    )

    response = cf.describe_stacks(
        StackName=STACK_NAME
    )

    outputs = {}

    for item in response["Stacks"][0].get("Outputs", []):
        outputs[item["OutputKey"]] = item["OutputValue"]

    return outputs


def wait_for_gateway(control, gateway_id):
    for _ in range(60):
        response = control.get_gateway(
            gatewayIdentifier=gateway_id
        )

        status = response.get("status")

        print(f"Gateway status: {status}")

        if status == "READY":
            return response

        if status in {
            "FAILED",
            "CREATE_FAILED",
            "UPDATE_FAILED"
        }:
            raise RuntimeError(
                f"Gateway failed: {json.dumps(response, default=str)}"
            )

        time.sleep(5)

    raise TimeoutError("Gateway did not become READY.")


def find_gateway(control):
    paginator = control.get_paginator("list_gateways")

    for page in paginator.paginate():
        for gateway in page.get("items", []):
            if gateway.get("name") == GATEWAY_NAME:
                return gateway

    return None


def create_gateway(control, role_arn):
    response = control.create_gateway(
        name=GATEWAY_NAME,
        roleArn=role_arn,
        protocolType="MCP",
        authorizerType="NONE"
    )

    gateway = response

    gateway_id = (
        gateway.get("gatewayId")
        or gateway.get("id")
    )

    if not gateway_id:
        raise RuntimeError(
            f"Unable to determine gateway ID: {gateway}"
        )

    return wait_for_gateway(control, gateway_id)


def find_target(control, gateway_id):
    paginator = control.get_paginator("list_gateway_targets")

    for page in paginator.paginate(
        gatewayIdentifier=gateway_id
    ):
        for target in page.get("items", []):
            if target.get("name") == TARGET_NAME:
                return target

    return None


def create_target(control, gateway_id, lambda_arn):
    tool_definition = {
        "name": "create_bug_report",
        "description": (
            "Create a customer bug report after the assistant has collected "
            "description, reproduction steps, and environment."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the customer's bug."
                },
                "stepsToReproduce": {
                    "type": "string",
                    "description": "Steps needed to reproduce the bug."
                },
                "environment": {
                    "type": "string",
                    "description": (
                        "Customer environment such as browser, operating "
                        "system, device, or application version."
                    )
                }
            },
            "required": [
                "description",
                "stepsToReproduce",
                "environment"
            ]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string"
                },
                "ticketId": {
                    "type": "string"
                }
            },
            "required": [
                "status",
                "ticketId"
            ]
        }
    }

    response = control.create_gateway_target(
        gatewayIdentifier=gateway_id,
        name=TARGET_NAME,
        description="Customer bug report Lambda target.",
        targetConfiguration={
            "mcp": {
                "lambda": {
                    "lambdaArn": lambda_arn,
                    "toolSchema": {
                        "inlinePayload": json.dumps(
                            [tool_definition]
                        )
                    }
                }
            }
        },
        credentialProviderConfigurations=[
            {
                "credentialProviderType": "GATEWAY_IAM_ROLE"
            }
        ]
    )

    return response


def main():
    outputs = get_stack_outputs()

    lambda_arn = outputs["LambdaArn"]
    gateway_role_arn = outputs["GatewayRoleArn"]
    harness_role_arn = outputs["HarnessExecutionRoleArn"]

    control = boto3.client(
        "bedrock-agentcore-control",
        region_name=REGION
    )

    gateway = find_gateway(control)

    if gateway:
        gateway_id = (
            gateway.get("gatewayId")
            or gateway.get("id")
        )

        gateway = wait_for_gateway(
            control,
            gateway_id
        )
    else:
        gateway = create_gateway(
            control,
            gateway_role_arn
        )

        gateway_id = (
            gateway.get("gatewayId")
            or gateway.get("id")
        )

    target = find_target(
        control,
        gateway_id
    )

    if not target:
        print("Creating Gateway Lambda target...")
        target = create_target(
            control,
            gateway_id,
            lambda_arn
        )

    gateway_arn = gateway["gatewayArn"]

    config = {
        "region": REGION,
        "gateway_name": GATEWAY_NAME,
        "gateway_id": gateway_id,
        "gateway_arn": gateway_arn,
        "target_name": TARGET_NAME,
        "lambda_arn": lambda_arn,
        "harness_execution_role_arn": harness_role_arn
    }

    with open(
        "agentcore_config.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(config, f, indent=2)

    print()
    print("Gateway configuration saved to agentcore_config.json")
    print(f"Gateway ARN: {gateway_arn}")
    print(f"Target: {TARGET_NAME}")


if __name__ == "__main__":
    main()
