try:
    import unzip_requirements
except ImportError:
    pass
import json
import os
import tushare as ts

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)

def get_index_data(event, context):
    request_data = json.loads(event['body'])
    ts_code = request_data['ts_code']
    start_date = request_data['start_date']
    end_date = request_data['end_Date']

    index_data = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    index_data = index_data.to_json()

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "index_data": index_data
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

    return response
