from __future__ import absolute_import
import tushare as ts
import pandas as pd
import tensorflow as tf
import numpy as np
import boto3
from datetime import date, datetime, timedelta
import os

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)
tf.enable_eager_execution()
s3 = boto3.resource('s3')

stock_A = "601939.SH"
stock_H = "00939.HK"
backword_length = 5
forword_length = 2
BATCH_SIZE = 16
BUFFER_SIZE = 10000
EPOCHS = 50
EVALUATION_INTERVAL = 200
end_date = date.today().strftime("%Y%m%d")
start_date = datetime.now() - timedelta(days=700)
start_date = start_date.strftime("%Y%m%d")

stock_data_A = pro.daily(ts_code=stock_A, start_date=start_date, end_date=end_date)

# prepare dataset
# 开高低收和成交量、涨跌值、振幅、均价、换手率
# use open high low close vol change pct_chg amount

stock_data_A_frame = pd.DataFrame(stock_data_A)
TRAIN_SPLIT = int(len(stock_data_A_frame) * 0.7)
data = []
label = []

open_mean = stock_data_A_frame['open'][:TRAIN_SPLIT].mean()
high_mean = stock_data_A_frame['high'][:TRAIN_SPLIT].mean()
low_mean = stock_data_A_frame['low'][:TRAIN_SPLIT].mean()
close_mean = stock_data_A_frame['close'][:TRAIN_SPLIT].mean()
vol_mean = stock_data_A_frame['vol'][:TRAIN_SPLIT].mean()
change_mean = stock_data_A_frame['change'][:TRAIN_SPLIT].mean()
pct_chg_mean = stock_data_A_frame['pct_chg'][:TRAIN_SPLIT].mean()
amount_mean = stock_data_A_frame['amount'][:TRAIN_SPLIT].mean()

open_std = stock_data_A_frame['open'][:TRAIN_SPLIT].std()
high_std = stock_data_A_frame['high'][:TRAIN_SPLIT].std()
low_std = stock_data_A_frame['low'][:TRAIN_SPLIT].std()
close_std = stock_data_A_frame['close'][:TRAIN_SPLIT].std()
vol_std = stock_data_A_frame['vol'][:TRAIN_SPLIT].std()
change_std = stock_data_A_frame['change'][:TRAIN_SPLIT].std()
pct_chg_std = stock_data_A_frame['pct_chg'][:TRAIN_SPLIT].std()
amount_std = stock_data_A_frame['amount'][:TRAIN_SPLIT].std()

for index, row in stock_data_A_frame.iterrows():
    if index < (len(stock_data_A_frame) - backword_length - forword_length):
        single_data = []
        for i in range(backword_length):
            data_row = stock_data_A_frame.iloc[index + i]
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
            predict_row = stock_data_A_frame.iloc[index + j]
            if predict_row['change'] > 0:
                single_predict.append(1)
            else:
                single_predict.append(0)
        label.append(single_predict)

train_x = data
train_y = label

train_data_single = tf.data.Dataset.from_tensor_slices((train_x, train_y))
train_data_single = train_data_single.cache().shuffle(BUFFER_SIZE).batch(1).repeat()

# define model
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

current_path = os.getcwd()
model.save(current_path + "/model.h5", include_optimizer=False)
s3.meta.client.upload_file(current_path + "/model.h5", 'wyqdatabase', 'model.h5')

predict_data = []
for i in range(backword_length):
    predict_row = stock_data_A_frame.iloc[len(stock_data_A_frame) - backword_length + i]
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

current_date = datetime.now() + timedelta(days=1)
current_date = current_date.strftime("%Y%m%d")
next_week = datetime.now() + timedelta(days=7)
next_week = next_week.strftime("%Y%m%d")
cal = pro.query('trade_cal', start_date=current_date, end_date=next_week)
cal = pd.DataFrame(cal)
cal = cal[cal.is_open == 1]
next_trade_date = cal.iloc[0]['cal_date']
