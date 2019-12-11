try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
import boto3
from botocore.exceptions import ClientError
dynamodb = boto3.resource('dynamodb')


def query_answer(event, context):
    data = json.loads(event['body'])

    corpora_table = dynamodb.Table(os.environ['ANSWER_TABLE'])
    try:
        response = corpora_table.get_item(Key={
            'request_id': data['request_id']
        })
        print(response)
        res = {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }
    except ClientError as e:
        print(e.response['Error']['Message'])
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
