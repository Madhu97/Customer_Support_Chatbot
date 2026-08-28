import json
import uuid

import boto3


class AgentCoreHarnessClient:

    def __init__(
        self,
        config_path="agentcore_config.json",
        session_id=None
    ):
        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as f:
            config = json.load(f)

        self.region = config.get(
            "region",
            "us-east-1"
        )

        self.harness_arn = config[
            "harness_arn"
        ]

        self.client = boto3.client(
            "bedrock-agentcore",
            region_name=self.region
        )

        self.session_id = (
            session_id
            or self.new_session_id()
        )

    @staticmethod
    def new_session_id():
        return str(uuid.uuid4())

    def invoke(self, message):
        response = self.client.invoke_harness(
            harnessArn=self.harness_arn,
            runtimeSessionId=self.session_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": message
                        }
                    ]
                }
            ]
        )

        return response

    @staticmethod
    def extract_text(response):
        if isinstance(response, str):
            return response

        if "stream" in response:
            parts = []

            for event in response["stream"]:
                if isinstance(event, dict):
                    parts.append(
                        AgentCoreHarnessClient.extract_text(
                            event
                        )
                    )

            return "".join(
                p for p in parts if p
            )

        if "output" in response:
            return AgentCoreHarnessClient.extract_text(
                response["output"]
            )

        if "message" in response:
            return AgentCoreHarnessClient.extract_text(
                response["message"]
            )

        if "content" in response:
            content = response["content"]

            if isinstance(content, list):
                return "".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict)
                )

        if "text" in response:
            return response["text"]

        return json.dumps(
            response,
            default=str
        )
