import json
import time

import boto3


REGION = "us-east-1"


def main():
    with open(
        "agentcore_config.json",
        "r",
        encoding="utf-8"
    ) as f:
        config = json.load(f)

    control = boto3.client(
        "bedrock-agentcore-control",
        region_name=REGION
    )

    harness_id = config.get("harness_id")
    gateway_id = config.get("gateway_id")

    if harness_id:
        print("Deleting harness...")

        try:
            control.delete_harness(
                harnessIdentifier=harness_id
            )
        except Exception as exc:
            print(f"Harness deletion warning: {exc}")

    if gateway_id:
        try:
            paginator = control.get_paginator(
                "list_gateway_targets"
            )

            targets = []

            for page in paginator.paginate(
                gatewayIdentifier=gateway_id
            ):
                targets.extend(
                    page.get("items", [])
                )

            for target in targets:
                target_id = target.get(
                    "gatewayTargetId"
                ) or target.get("id")

                if target_id:
                    print(
                        f"Deleting gateway target: "
                        f"{target_id}"
                    )

                    control.delete_gateway_target(
                        gatewayIdentifier=gateway_id,
                        targetId=target_id
                    )

        except Exception as exc:
            print(
                f"Gateway target deletion warning: {exc}"
            )

        print("Deleting gateway...")

        try:
            control.delete_gateway(
                gatewayIdentifier=gateway_id
            )
        except Exception as exc:
            print(
                f"Gateway deletion warning: {exc}"
            )

    print("AgentCore cleanup requested.")


if __name__ == "__main__":
    main()
