try:
  import unzip_requirements
except ImportError:
  pass
import tensorflow as tf
import tensorflow_hub as hub
import sentencepiece as spm
import numpy as np
import json
import logging
import boto3
import os

aws_lambda = boto3.client('lambda')


def compute_vector(event, context):
    data = json.loads(event['body'])
    if 'question' not in data or 'method' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't compute vector.")

    question = data['question']
    module = hub.Module("https://tfhub.dev/google/universal-sentence-encoder-lite/2")
    '''
    input_placeholder = tf.sparse_placeholder(tf.int64, shape=[None, None])
    encodings = module(
        inputs=dict(
            values=input_placeholder.values,
            indices=input_placeholder.indices,
            dense_shape=input_placeholder.dense_shape)
    )

    with tf.Session() as sess:
        spm_path = sess.run(module(signature="spm_path"))

    sp = spm.SentencePieceProcessor()
    sp.Load(spm_path)

    def process_to_IDs_in_sparse_format(sp, sentences):
        # An utility method that processes sentences with the sentence piece processor
        # 'sp' and returns the results in tf.SparseTensor-similar format:
        # (values, indices, dense_shape)
        ids = [sp.EncodeAsIds(x) for x in sentences]
        max_len = max(len(x) for x in ids)
        dense_shape = (len(ids), max_len)
        values = [item for sublist in ids for item in sublist]
        indices = [[row, col] for row in range(len(ids)) for col in range(len(ids[row]))]
        return (values, indices, dense_shape)

    messages = [question]
    values, indices, dense_shape = process_to_IDs_in_sparse_format(sp, messages)
    with tf.Session() as session:
        session.run([tf.global_variables_initializer(), tf.tables_initializer()])
        message_embeddings = session.run(
            encodings,
            feed_dict={input_placeholder.values: values,
                       input_placeholder.indices: indices,
                       input_placeholder.dense_shape: dense_shape})

        vector = np.array(message_embeddings).tolist()

    if data['method'] == 'add_copora':
        # run lambda function add_copora
        body = json.dumps({
           "question": data['question'],
           "answer": data['answer'],
           "copora_id": data['copora_id'],
           "vector": vector
        })
        print("add copora function name: {}".format(os.environ['ADD_COPORA']))
        response = aws_lambda.invoke(
            FunctionName=os.environ['ADD_COPORA'],
            Payload=body
        )
        res = {
            "statusCode": 200,
            "body": body,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }
        return res
    else:
        # run lambda function compute answer
        body = json.dumps({
            "question": data['question'],
            "vector": vector
        })
    '''
    res = {
        "statusCode": 200,
        "body": "running right!",
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }
    return res




