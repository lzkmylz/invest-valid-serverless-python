try:
    import unzip_requirements
except ImportError:
    pass
import os
import tushare as ts
import json
import numpy as np
from datetime import date, datetime, timedelta
import statsmodels.api as sm

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)

def rsrs_compute(event, context):
    request_data = json.loads(event['body'])
    stock = request_data['stock']
    end_date = date.today().strftime("%Y%m%d")
    start_date = datetime.now() - timedelta(days=30)
    start_date = start_date.strftime("%Y%m%d")

    stock_data = pro.daily(ts_code=stock, start_date=start_date, end_date=end_date)
    high = np.array(stock_data['high'])
    low = np.array(stock_data['low'])

    x = sm.add_constant(low)
    y = high
    model = sm.OLS(y, x).fit()
    result = model.params[1]

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "score": result
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

    return response
