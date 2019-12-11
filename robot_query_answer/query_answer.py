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
        item = response['Item']
        if len(item) > 0:
            res = {
                "statusCode": 200,
                "body": json.dumps({
                    "question": item['question'],
                    "answer": item['answer'],
                    "corpora_question": item['corpora_question'],
                    "request_id": item['request_id']
                }),
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true"
                }
            }
        else:
            res = {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Data not found"
                }),
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true"
                }
            }
    except ClientError as e:
        print(e.response['Error']['Message'])
        res = {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }

    return res
