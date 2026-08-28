import json
import time

import boto3


REGION = "us-east-1"
HARNESS_NAME = "customer-support-chatbot"

MODEL_ID = "us.amazon.nova-pro-v1:0"

CONFIG_FILE = "agentcore_config.json"


def load_config():
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def build_prompt():
    with open(
        "system_prompt.txt",
        "r",
        encoding="utf-8"
    ) as f:
        prompt = f.read()

    with open(
        "online_shop_faq.md",
        "r",
        encoding="utf-8"
    ) as f:
        faq = f.read()

    return prompt.replace(
        "{{FAQ}}",
        faq
    )


def find_harness(control):
    paginator = control.get_paginator(
        "list_harnesses"
    )

    for page in paginator.paginate():
        for harness in page.get(
            "harnesses",
            page.get("items", [])
        ):
            if harness.get("harnessName") == HARNESS_NAME:
                return harness

    return None


def wait_for_ready(control, harness_id):
    for _ in range(60):
        result = control.get_harness(
            harnessIdentifier=harness_id
        )

        status = result.get("status")

        print(f"Harness status: {status}")

        if status == "READY":
            return result

        if status in {
            "CREATE_FAILED",
            "UPDATE_FAILED",
            "DELETE_FAILED"
        }:
            raise RuntimeError(
                f"Harness failed: {json.dumps(result, default=str)}"
            )

        time.sleep(5)

    raise TimeoutError(
        "Harness did not become READY."
    )


def main():
    config = load_config()

    role_arn = config[
        "harness_execution_role_arn"
    ]

    gateway_arn = config["gateway_arn"]

    control = boto3.client(
        "bedrock-agentcore-control",
        region_name=REGION
    )

    tools = [
        {
            "type": "agentcore_gateway",
            "name": "bugreports",
            "config": {
                "agentCoreGateway": {
                    "gatewayArn": gateway_arn,
                    "outboundAuth": {
                        "awsIam": {}
                    }
                }
            }
        }
    ]

    allowed_tools = [
        "@bugreports/*"
    ]

    kwargs = {
        "executionRoleArn": role_arn,
        "systemPrompt": [
            {
                "text": build_prompt()
            }
        ],
        "tools": tools,
        "allowedTools": allowed_tools,
        "maxIterations": 10,
        "maxTokens": 1200,
        "timeoutSeconds": 120,
        "model": {
            "bedrockModelConfig": {
                "modelId": MODEL_ID
            }
        }
    }

    existing = find_harness(control)

    if existing:
        harness_id = existing["harnessId"]

        print(
            f"Updating existing harness: {harness_id}"
        )

        control.update_harness(
            harnessIdentifier=harness_id,
            **kwargs
        )
    else:
        print("Creating harness...")

        response = control.create_harness(
            harnessName=HARNESS_NAME,
            **kwargs
        )

        harness_id = response[
            "harness"
        ]["harnessId"]

    result = wait_for_ready(
        control,
        harness_id
    )

    config["harness_id"] = result["harnessId"]
    config["harness_arn"] = result["arn"]
    config["model_id"] = MODEL_ID

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(config, f, indent=2)

    print()
    print("Harness is READY.")
    print(f"Harness ARN: {result['arn']}")


if __name__ == "__main__":
    main()
