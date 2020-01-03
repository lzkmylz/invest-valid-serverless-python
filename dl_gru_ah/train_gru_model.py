try:
    import unzip_requirements
except ImportError:
    pass
import boto3
import tushare as ts
import tensorflow as tf
import pandas as pd
import numpy as np
import uuid
from datetime import date, datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
import os

dynamodb = boto3.resource('dynamodb')
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
predict_table = dynamodb.Table(os.environ['GRU_PREDICT_TABLE'])


def train_gru_model(event, context):
    current_date = datetime.now() + timedelta(days=1)
    current_date = current_date.strftime("%Y%m%d")
    next_week = datetime.now() + timedelta(days=7)
    next_week = next_week.strftime("%Y%m%d")
    cal = pro.query('trade_cal', start_date=current_date, end_date=next_week)
    cal = pd.DataFrame(cal)
    cal = cal[cal.is_open == 1]
    next_trade_date_1 = cal.iloc[0]['cal_date']
    next_trade_date_2 = cal.iloc[1]['cal_date']
    update_next_day_1 = True
    update_next_day_2 = True

    stock_name = event['stock_name']
    stock_data = pro.daily(ts_code=stock_name, start_date=start_date, end_date=end_date)

    response = predict_table.scan(IndexName="stockName", FilterExpression=Key('stock_name').eq(stock_name) & (Attr("trade_date").eq(next_trade_date_1) | Attr("trade_date").eq(next_trade_date_2)))
    items = response['Items']
    if len(items) > 1:
        print("Already predicted, skip training model and predict.")
        return
    if len(items) == 1:
        update_next_day_1 = False
        print("Skip update next 1 trade day predict.")

    # prepare dataset
    # 开高低收和成交量、涨跌值、振幅、均价、换手率
    # use open high low close vol change pct_chg amount
    data = []
    label = []
    stock_data_frame = pd.DataFrame(stock_data)

    open_mean = stock_data_frame['open'].mean()
    high_mean = stock_data_frame['high'].mean()
    low_mean = stock_data_frame['low'].mean()
    close_mean = stock_data_frame['close'].mean()
    vol_mean = stock_data_frame['vol'].mean()
    change_mean = stock_data_frame['change'].mean()
    pct_chg_mean = stock_data_frame['pct_chg'].mean()
    amount_mean = stock_data_frame['amount'].mean()

    open_std = stock_data_frame['open'].std()
    high_std = stock_data_frame['high'].std()
    low_std = stock_data_frame['low'].std()
    close_std = stock_data_frame['close'].std()
    vol_std = stock_data_frame['vol'].std()
    change_std = stock_data_frame['change'].std()
    pct_chg_std = stock_data_frame['pct_chg'].std()
    amount_std = stock_data_frame['amount'].std()

    for index, row in stock_data_frame.iterrows():
        if index < (len(stock_data_frame) - backword_length - forword_length):
            single_data = []
            for i in range(backword_length):
                data_row = stock_data_frame.iloc[index + i]
                single_row_data = [
                    (data_row['open'] - open_mean) / open_std,
                    (data_row['high'] - high_mean) / high_std,
                    (data_row['low'] - low_mean) / low_std,
                    (data_row['close'] - close_mean) / close_std,
                    (data_row['vol'] - vol_mean) / vol_std,
                    (data_row['change'] - change_mean) / change_std,
                    (data_row['pct_chg'] - pct_chg_mean) / pct_chg_std,
                    (data_row['amount'] - amount_mean) / amount_std
                ]
                single_data.append(single_row_data)
            data.append(single_data)

            single_predict = []
            for j in range(backword_length, backword_length + forword_length):
                predict_row = stock_data_frame.iloc[index + j]
                if predict_row['change'] > 0:
                    single_predict.append(1)
                else:
                    single_predict.append(0)
            label.append(single_predict)

    train_data_single = tf.data.Dataset.from_tensor_slices((data, label))
    train_data_single = train_data_single.cache().shuffle(BUFFER_SIZE).batch(1).repeat()

    model = tf.keras.Sequential()
    model.add(tf.keras.layers.LSTM(128, input_shape=(backword_length, 8), return_sequences=True))
    model.add(tf.keras.layers.Dropout(0.2))
    model.add(tf.keras.layers.LSTM(256, return_sequences=False))
    model.add(tf.keras.layers.Dropout(0.2))
    model.add(tf.keras.layers.Dense(128, activation="relu"))
    model.add(tf.keras.layers.Dropout(0.2))
    model.add(tf.keras.layers.Dense(forword_length, activation="sigmoid"))
    model.compile(optimizer=tf.keras.optimizers.RMSprop(), loss='mae', metrics=['accuracy'])

    model_history = model.fit(train_data_single, epochs=EPOCHS,
                              steps_per_epoch=EVALUATION_INTERVAL)

    # do predict
    predict_data = []
    for i in range(backword_length):
        predict_row = stock_data_frame.iloc[len(stock_data_frame) - backword_length + i]
        predict_row_data = [
            (predict_row['open'] - open_mean) / open_std,
            (predict_row['high'] - high_mean) / high_std,
            (predict_row['low'] - low_mean) / low_std,
            (predict_row['close'] - close_mean) / close_std,
            (predict_row['vol'] - vol_mean) / vol_std,
            (predict_row['change'] - change_mean) / change_std,
            (predict_row['pct_chg'] - pct_chg_mean) / pct_chg_std,
            (predict_row['amount'] - amount_mean) / amount_std
        ]
        predict_data.append(predict_row_data)
    predict_data = np.array(predict_data)
    predict_data = np.expand_dims(predict_data, axis=0)
    result = model.predict(predict_data)
    result[result >= 0.5] = 1
    result[result < 0.5] = 0

    # query trade calendar
    if update_next_day_1:
        item1_id = str(uuid.uuid4())
        item1 = {
            "id": item1_id,
            "stock_name": stock_name,
            "trade_date": next_trade_date_1,
            "predict_result": int(result[0][0])
        }
        predict_table.put_item(Item=item1)
    if update_next_day_2:
        item2_id = str(uuid.uuid4())
        item2 = {
            "id": item2_id,
            "stock_name": stock_name,
            "trade_date": next_trade_date_2,
            "predict_result": int(result[0][1])
        }
        predict_table.put_item(Item=item2)
