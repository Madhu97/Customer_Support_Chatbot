import os
import uuid
import boto3


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    description = event.get("description")
    steps = event.get("stepsToReproduce")
    environment = event.get("environment")

    missing = []

    if not description:
        missing.append("description")

    if not steps:
        missing.append("stepsToReproduce")

    if not environment:
        missing.append("environment")

    if missing:
        return {
            "status": "ERROR",
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    ticket_id = f"BUG-{uuid.uuid4().hex[:10].upper()}"

    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps,
        "environment": environment,
        "status": "OPEN"
    }

    table.put_item(Item=item)

    return {
        "status": "OPEN",
        "ticketId": ticket_id
    }
