#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt

import talib

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

from asset_selection import my_asset_selection

pd.set_option('display.max_rows', None)  # 设置Pandas显示的行数
pd.set_option('display.width', None)  # 设置Pandas显示的宽度

short = 30  # 短周期
long = 60  # 长周期

data_length = long + 2  # k线数据长度
# "duration_seconds=60"为一分钟线, 日线的duration_seconds参数为: 24*60*60
symbol = 'SHFE.rb1905'

# api = TqApi('SIM')
# home PC
api = TqApi('SIM', url='ws://192.168.50.1:7777')
quote = api.get_quote(symbol)
klines = api.get_kline_serial(symbol, duration_seconds=10, data_length=data_length)
target_pos = TargetPosTask(api, symbol)
account = api.get_account()
position = api.get_position(symbol)

with closing(api):
    while True:
        api.wait_update()
        if api.is_changing(klines[-1], 'datetime'):
            # 等待新的K线生成
            api.wait_update()
            now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
            print(now)

            short_avg = talib.SMA(np.array(klines.close), timeperiod=short)  # 短周期
            long_avg = talib.SMA(np.array(klines.close), timeperiod=long)  # 长周期

            # 均线下穿，做空
            if long_avg[-2] < short_avg[-2] and long_avg[-1] > short_avg[-1]:
                target_pos.set_target_volume(-3)
                print("均线下穿，做空")
            # 均线上穿，做多
            if short_avg[-2] < long_avg[-2] and short_avg[-1] > long_avg[-1]:
                target_pos.set_target_volume(3)
                print("均线上穿，做多")

        if api.is_changing(account, 'float_profit'):
            print('浮动盈亏：', account['float_profit'])
            print('多头持仓盈亏', symbol, ':', position['position_profit_long'])
            print('空头持仓盈亏', symbol, ':', position['position_profit_short'])

