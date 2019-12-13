import tushare as ts
import pandas as pd
from datetime import date, datetime, timedelta
import os

token = os.environ['TUSHARE_TOKEN']
pro = ts.pro_api(token)


stock_A = "601939.SH"
stock_H = "00939.HK"
end_date = date.today().strftime("%Y%m%d")
start_date = datetime.now() - timedelta(days=90)
start_date = start_date.strftime("%Y%m%d")

stock_data_A = pro.daily(ts_code=stock_A, start_date=start_date, end_date=end_date)
stock_data_H = pro.hk_daily(ts_code=stock_H, start_date=start_date, end_date=end_date)

# prepare dataset
# 开高低收和成交量、涨跌值、振幅、均价、换手率
# use open high low close vol change pct_chg amount

stock_data_A_frame = pd.DataFrame(stock_data_A)
stock_data_H_frame = pd.DataFrame(stock_data_H)
stock_data_A_processed = {}
stock_data_H_processed = {}
for index, row in stock_data_A_frame.iterrows():
    stock_data_A_processed[row['trade_date']] = \
        [row['open'], row['high'], row['low'], row['close'],
         row['vol'], row['change'], row['pct_chg'], row['amount']]

for index, row in stock_data_H_frame.iterrows():
    stock_data_H_processed[row['trade_date']] = \
        [row['open'], row['high'], row['low'], row['close'],
         row['vol'], row['change'], row['pct_chg'], row['amount']]
