try:
    import unzip_requirements
except ImportError:
    pass

import json
import boto3
import os
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')

def compute_vector(event, context):
    data = event

    request_id = data['id']
    question = data['question']
    corpora_id = data['copora_id']
    print(type(data['vector']))
    vector = np.array(json.dumps(data['vector']))
    print(vector.size())

    corpora_table = dynamodb.Table(os.environ['CORPORA_TABLE'])
    response = corpora_table.scan(FilterExpression=Attr('copora_id').eq(corpora_id))
    items = response['Items']
    print(items)

    corpora_vectors = np.zeros((len(items), 512))
    print(corpora_vectors.size())
    for i in range(len(items)):
        corpora_vectors[i, :] = np.array(json.dumps(items[i]['vector']))
    corr = cosine_similarity(corpora_vectors, vector)
    target_ind = np.argmax(corr)
    target_item = items[target_ind]

    answer_table = dynamodb.Table(os.environ['ANSWER_TABLE'])
    expire_time = int(time.time() + 3600)
    item = {
        'request_id': request_id,
        'question': question,
        'answer': target_item['answer'],
        'corpora_question': target_item['question'],
        'ttl': expire_time
    }
    answer_table.put_item(Item=item)
