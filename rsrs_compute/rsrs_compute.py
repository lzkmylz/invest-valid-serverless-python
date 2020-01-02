try:
    import unzip_requirements
except ImportError:
    pass
import os
import tushare as ts
import json

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)

def rsrs_compute(event, context):

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "score": 1
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

    return response
