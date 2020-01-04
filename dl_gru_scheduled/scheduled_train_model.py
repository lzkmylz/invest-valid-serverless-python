try:
    import unzip_requirements
except ImportError:
    pass
import boto3
import json
import os

aws_lambda = boto3.client('lambda')


def scheduled_train_model(event, context):
    stock_list = ["601939.SH", "600276.SH", "600340.SH", "000415.SZ"]

    for i in range(len(stock_list)):
        payload = json.dumps({
            "stock_name": stock_list[i]
        })
        aws_lambda.invoke(
            FunctionName=os.environ['SCHEDULED_TRAIN_MODEL'],
            Payload=payload,
            InvocationType='Event'
        )


'''
    aws_lambda.invoke(
        FunctionName=os.environ['SCHEDULED_TRAIN_INDEX_MODEL'],
        InvocationType='Event'
    )
'''

