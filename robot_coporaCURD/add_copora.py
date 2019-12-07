try:
    import unzip_requirements
except ImportError:
    pass
import json
import logging
import os
import uuid
from datetime import datetime

import boto3
dynamodb = boto3.resource('dynamodb')


def add_copora(event, context):
    data = json.loads(event)
    if 'question' not in data or 'answer' not in data or 'vector' not in data or 'corpora_id' not in data:
        logging.error("Validation Failed")
        print(data)
        raise Exception("Couldn't create the copora item.")

    timestamp = str(datetime.utcnow().timestamp())
    table = dynamodb.Table(os.environ['COPORA_TABLE'])
    item = {
        'id': str(data['id']),
        'corpora_id': str(data['corpora_id']),
        'question': str(data['question']),
        'answer': str(data['answer']),
        'vector': str(data['vector']),
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    table.put_item(Item=item)
    response = {
        "statusCode": 200,
        "body": json.dumps(item),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

    return response
