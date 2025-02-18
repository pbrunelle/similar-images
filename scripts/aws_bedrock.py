import base64
import json
import logging
import os

import boto3
import fire


def bedrock(path: str, query: str, model: str = "amazon.nova-lite-v1:0"):
    session = boto3.Session()
    bedrock_runtime = session.client(service_name="bedrock-runtime")
    with open(path, "rb") as f:
        file = base64.b64encode(f.read()).decode("ascii")
    message_content = [
        {
            "image": {
                "format": path.split(".")[-1],
                "source": {
                    "bytes": file,
                },
            }
        },
        {"text": query},
    ]
    payload = {
        "messages": [{"role": "user", "content": message_content}],
        "inferenceConfig":{"maxTokens":2000}
    }
    response = bedrock_runtime.invoke_model(
        body=json.dumps(payload),
        modelId=model,
        accept="application/json",
        contentType="application/json",
    )
    print(response)
    try:
        response_body = json.loads(response["body"].read().decode("utf-8"))
        answer = response_body["output"]["message"]["content"][0]["text"]
        print(answer)
    except Exception as e:
        print(response)
        print(f"{type(e)} {e}")


if __name__ == "__main__":
    fire.Fire(bedrock)
