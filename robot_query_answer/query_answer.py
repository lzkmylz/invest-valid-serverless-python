try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb')

def query_answer(event, context):
    data = json.loads(event['body'])

    corpora_table = dynamodb.Table(os.environ['CORPORA_TABLE'])
    key = {
        "request_id": {
            "S": data['request_id']
        }
    }
    response = corpora_table.get_item(Key=key)
    print(response)

    if len(response) > 0:
        res = {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }
    else:
        res = {
            "statusCode": 404,
            "body": json.dumps({
                "message": "Answer not found."
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }
    return res