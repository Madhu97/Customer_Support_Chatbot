#!/usr/bin/env bash

set -euo pipefail

REGION="us-east-1"

INPUT="output_eval_dataset.jsonl"

if [ ! -f "$INPUT" ]; then
    echo "Evaluation dataset not found."
    echo "Run:"
    echo "  python generate-eval-dataset.py"
    exit 1
fi

echo "Evaluation dataset:"
wc -l "$INPUT"

echo
echo "Upload this file to the S3 bucket created by:"
echo "  cloudformation-testing.yaml"
echo
echo "Example:"
echo "  aws s3 cp $INPUT s3://<evaluation-bucket>/output_eval_dataset.jsonl --region $REGION"
echo
echo "Then create the Bedrock Evaluation job from the Amazon Bedrock console"
echo "using the uploaded JSONL prompt dataset and an LLM-as-a-judge evaluator."
