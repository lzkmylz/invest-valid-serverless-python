try:
  import unzip_requirements
except ImportError:
  pass
import boto3
import json
import logging
import os
import uuid

aws_lambda = boto3.client('lambda')

def compute_vector(event, context):
    data = json.loads(event['body'])
    if 'question' not in data or 'method' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't compute vector.")

    id = uuid.uuid4()

    if data['method'] == "add_corpora":
        req_body = {
            "question": data['question'],
            "answer": data['answer'],
            "corpora_id": data['corpora_id'],
            "id": id
        }
    if data['method'] == "compute_answer":
        req_body = {
            "question": data['question'],
            "corpora_id": data['corpora_id'],
            "id": id
        }

    aws_lambda.invoke(
        FunctionName=os.environ['COMPUTE_VECTOR'],
        Payload=req_body,
        InvocationType='event'
    )

    res_body = {
        "request_id": id
    }

    res = {
        "statusCode": 200,
        "body": json.dumps(res_body),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }
    return res