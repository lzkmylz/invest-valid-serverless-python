import tushare as ts
import pandas as pd
from datetime import date, datetime, timedelta
import os

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)


stock_A = "601939.SH"
stock_H = "00939.HK"
backword_length = 5
end_date = date.today().strftime("%Y%m%d")
start_date = datetime.now() - timedelta(days=200)
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
    if index < (len(stock_data_A_frame) - backword_length):
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
        predict_row = stock_data_A_frame.iloc[index + backword_length]
        label.append(predict_row['change'])

train_x = data[:TRAIN_SPLIT]
train_y = label[:TRAIN_SPLIT]
test_x = data[TRAIN_SPLIT:]
test_y = label[TRAIN_SPLIT:]


