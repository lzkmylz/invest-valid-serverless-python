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
        if 'Item' in response.keys():
            item = response['Item']
        else:
            item = "Data not found"
        res = {
            "statusCode": 200,
            "body": json.dumps(item),
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
