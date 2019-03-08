#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

from trading_strategies.technical_indicators import MACD_adj



SYMBOL = 'SHFE.rb1905'
CLOSE_HOUR, CLOSE_MINUTE = 14, 50  # 平仓时间

api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,3,6)))
# api = TqApi('SIM')
quote = api.get_quote(SYMBOL)
klines_15 = api.get_kline_serial(SYMBOL, duration_seconds=15*60)
klines_1 = api.get_kline_serial(SYMBOL, duration_seconds=60)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价

account = api.get_account()

with closing(api):
    while True:
        target_pos.set_target_volume(target_pos_value)
        api.wait_update()
        if api.is_changing(klines_15[-1], 'datetime'):

            k15 = str(dt.datetime.fromtimestamp(klines_15.datetime[-1] / 1e9))
            print(k15)

            ys = pd.Series(data=klines_15.close[-40:],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines_15.datetime[-40:]]
                           )
            dict_results = MACD_adj(ys)

            if target_pos_value == 0:
                # 上涨阶段金叉 做多
                if dict_results['signal'] == 1:
                    target_pos_value = 2
                    print("上涨阶段金叉 做多")
                # 下跌阶段死叉，做空
                if dict_results['signal'] == -1:
                    target_pos_value = -2
                    print("下跌阶段死叉，做空")

            if (target_pos_value > 0 and (dict_results['MACD'][-1] - dict_results['SL'][-1]) <
                    (dict_results['MACD'][-2] - dict_results['SL'][-2])) or \
                    (target_pos_value < 0 and (dict_results['MACD'][-1] - dict_results['SL'][-1]) >
                     (dict_results['MACD'][-2] - dict_results['SL'][-2])):
                target_pos_value = 0
                print('止损平仓')

        if api.is_changing(quote, 'datetime'):
            # print("最新价: ", quote['datetime'])
            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 2) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 2):
                target_pos_value = 0
                print('止盈平仓')