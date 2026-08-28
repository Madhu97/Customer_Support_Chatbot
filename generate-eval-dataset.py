import json
from pathlib import Path

from agentcore_client import AgentCoreHarnessClient


INPUT_FILE = "flow-tests.json"
OUTPUT_FILE = "output_eval_dataset.jsonl"


def main():
    tests = json.loads(
        Path(INPUT_FILE).read_text(
            encoding="utf-8"
        )
    )

    output_lines = []

    for test in tests:

        client = AgentCoreHarnessClient()

        response = client.invoke(
            test["input"]
        )

        assistant_text = client.extract_text(
            response
        )

        record = {
            "prompt": test["input"],
            "referenceResponse": (
                test["expected_behavior"]
            ),
            "category": test["category"],
            "modelResponse": assistant_text
        }

        output_lines.append(
            json.dumps(
                record,
                ensure_ascii=False
            )
        )

    Path(OUTPUT_FILE).write_text(
        "\n".join(output_lines) + "\n",
        encoding="utf-8"
    )

    print(
        f"Wrote {len(output_lines)} evaluation records "
        f"to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
