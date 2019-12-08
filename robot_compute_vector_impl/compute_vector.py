try:
    import unzip_requirements
except ImportError:
    pass
import tensorflow as tf
import tensorflow_hub as hub
import sentencepiece as spm
import numpy as np
import json
import boto3
import os

aws_lambda = boto3.client('lambda')


def compute_vector(event, context):
    data = event

    question = data['question']
    module = hub.Module("https://tfhub.dev/google/universal-sentence-encoder-lite/2")

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

    def process_to_ids_in_sparse_format(sp, sentences):
        ids = [sp.EncodeAsIds(x) for x in sentences]
        max_len = max(len(x) for x in ids)
        dense_shape = (len(ids), max_len)
        values = [item for sublist in ids for item in sublist]
        indices = [[row, col] for row in range(len(ids)) for col in range(len(ids[row]))]
        return (values, indices, dense_shape)

    messages = [question]
    values, indices, dense_shape = process_to_ids_in_sparse_format(sp, messages)
    with tf.Session() as session:
        session.run([tf.global_variables_initializer(), tf.tables_initializer()])
        message_embeddings = session.run(
            encodings,
            feed_dict={input_placeholder.values: values,
                       input_placeholder.indices: indices,
                       input_placeholder.dense_shape: dense_shape})

        vector = np.array(message_embeddings).tolist()

    if data['method'] == 'add_corpora':
        # run lambda function add_corpora
        body = json.dumps({
            "question": data['question'],
            "answer": data['answer'],
            "corpora_id": data['corpora_id'],
            "id": data['id'],
            "vector": vector
        })
        print("add corpora function name: {}".format(os.environ['ADD_CORPORA']))
        aws_lambda.invoke(
            FunctionName=os.environ['ADD_CORPORA'],
            Payload=body,
            InvocationType='Event'
        )
    else:
        # run lambda function compute answer
        body = json.dumps({
            "id": data['id'],
            "question": data['question'],
            "corpora_id": data['corpora_id'],
            "vector": vector
        })
        aws_lambda.invoke(
            FunctionName=os.environ['COMPUTE_ANSWER'],
            Payload=body,
            InvocationType='Event'
        )
