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

api = TqApi('SIM')
quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, duration_seconds=60)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价

account = api.get_account()

with closing(api):
    while True:
        target_pos.set_target_volume(target_pos_value)
        api.wait_update()
        if api.is_changing(klines[-1], 'datetime'):
            # 等待新的K线生成
            api.wait_update()
            now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
            print(now)

            ys = pd.Series(data=klines.close[-40:],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-40:]]
                           )
            # print(ys)
            dict_results = MACD_adj(ys)
            print('diff', dict_results['MACD'][-1])
            print('SL', dict_results['SL'][-1])

            # 上涨阶段金叉 做多
            if dict_results['signal'] == 1:
                target_pos.set_target_volume(-1)
                print("上涨阶段金叉 做多")
            # 下跌阶段死叉，做空
            if dict_results['signal'] == -1:
                target_pos.set_target_volume(1)
                print("下跌阶段死叉，做空")

        # if api.is_changing(account, 'float_profit'):
        #     print('浮动盈亏：', account['float_profit'])
        #     if account['float_profit'] > 200:
        #         target_pos.set_target_volume(0)


