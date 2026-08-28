# Customer Support Chatbot with Amazon Bedrock AgentCore

## Architecture

Customer
   |
   v
chat.py
   |
   v
AgentCore Harness
   |
   +-- System Prompt
   |      |
   |      +-- BUG_REPORT
   |      +-- PLATFORM_FAQ
   |      +-- HUMAN_HANDOFF
   |
   +-- AgentCore Gateway
          |
          +-- bugreports
                 |
                 v
              Lambda
                 |
                 v
              DynamoDB


## AWS Region

All resources use:

    us-east-1

## Model

The project pins:

    us.amazon.nova-pro-v1:0

The harness should not rely on its default model.

## Prerequisites

- AWS account
- Bedrock access
- AgentCore access
- AWS CLI configured
- Python 3.10+
- boto3 1.43+
- Access to Amazon Nova Pro

## Install dependencies

```bash
pip install -r requirements.txt
