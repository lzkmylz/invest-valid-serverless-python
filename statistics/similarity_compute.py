try:
  import unzip_requirements
except ImportError:
  pass
import json
import os
import tushare as ts
import numpy as np
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)

def similarity_compute(event, context):
    request_data = json.loads(event['body'])
    stock1 = request_data['stock1']
    stock2 = request_data['stock2']
    start_date = request_data['startDate']
    end_date = request_data['endDate']

    adf_flag = False

    stock1_data = pro.daily(ts_code=stock1, start_date=start_date, end_date=end_date)
    stock2_data = pro.daily(ts_code=stock2, start_date=start_date, end_date=end_date)

    stock1_prices = np.array(stock1_data['close'])
    stock2_prices = np.array(stock2_data['close'])

    stock1_adf = adfuller(stock1_prices)
    stock2_adf = adfuller(stock2_prices)

    if stock1_adf[0] > stock1_adf[4]['5%']:
        adf_flag = True
    if stock2_adf[0] > stock2_adf[4]['5%']:
        adf_flag = True

    if adf_flag:
        response = {
            "statusCode": 200,
            "body": json.dumps({
                "score": 0
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        }
        return response

    x = sm.add_constant(stock1_prices)
    y = stock2_prices
    model = sm.OLS(y, x)
    results = model.fit()
    params = results.params
    alpha = params[0]
    beta = params[1]
    sigma = np.abs(np.mean(stock1_prices - (stock2_prices * alpha + beta)))
    score = (1 - sigma / np.mean(stock1_prices)) * 100

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "score": score
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    }

    return response
