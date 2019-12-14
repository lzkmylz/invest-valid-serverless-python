try:
    import unzip_requirements
except ImportError:
    pass
import boto3
import tushare as ts
import tensorflow as tf
from datetime import date, datetime, timedelta
import os

s3 = boto3.resource('s3')
token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)
backword_length = 5
forword_length = 2
BATCH_SIZE = 16
BUFFER_SIZE = 10000
EPOCHS = 50
EVALUATION_INTERVAL = 200
end_date = date.today().strftime("%Y%m%d")
start_date = datetime.now() - timedelta(days=700)
start_date = start_date.strftime("%Y%m%d")

def train_gru_model(event, context):
    stock_name = event['stock_name']
    stock_data = pro.daily(ts_code=stock_name, start_date=start_date, end_date=end_date)

