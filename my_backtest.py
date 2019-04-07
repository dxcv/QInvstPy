#  -*- coding: utf-8 -*-
"""
@author: chen zhang
"""

import os

import numpy as np
import pandas as pd
import datetime as dt

pd.set_option('display.max_rows', None)  # 设置Pandas显示的行数
pd.set_option('display.width', None)  # 设置Pandas显示的宽度

######################################################################
# 确定交易品种、合约和交易时间
######################################################################
from trading_selection import my_assets_selection
from trading_selection import symbols_selection
# 确定交易品种和合约
dict_assets = my_assets_selection()
print('交易方向：')
print('多头品种：', dict_assets['long'])
print('空头品种：', dict_assets['short'])

ls_long_assets = dict_assets['long']
ls_short_assets = dict_assets['short']

dict_symbols = symbols_selection(dict_assets)
print('交易合约：')
print('多头合约：', dict_symbols['long'])
print('空头合约：', dict_symbols['short'])

ls_long_symbols = dict_symbols['long']
ls_short_symbols = dict_symbols['short']
# TODO: 交易规则 不同品种不一样。。
# eg., rb
long_asset = ls_long_assets[0]

# 确定交易合约的交易时间
close_hour_day, close_minute_day = 14, 54  # 预定收盘时间(因为真实收盘后无法进行交易, 所以提前设定收盘时间)
# close_hour, close_minute = 10, 14
close_hour_night, close_minute_night = 22, 56
# close_hour, close_minute = 23, 30

######################################################################
# 确定K线参数 回测周期参数
######################################################################
# set time interval
# say 5分钟K线
# select_time_interval: 5min 15min 1d
# based on the trading break: 10:15-10:29, hard to adjust time interval
duration_seconds = 5 * 60
# duration_seconds = 15 * 60
# duration_seconds = 24 * 60 * 60

# backtest period
start_date = dt.date(2018, 7, 2)
end_date = dt.date(2018, 7, 26)
# aware of some special cases, say 20161111

######################################################################
# 策略编写与导入
######################################################################
from my_strategy import MyStrategy
my_strategy1 = MyStrategy()
'''
what analysis is used 
idea from XXX paper
'''

x = """
def BB(ys, w=20, k=2):

    BB_mid = SMA(ys, w)['SMA']

    # diff_square = (ys - BB_mid).apply(np.square)
    # sigma = (diff_square.rolling(window=w).mean()).apply(np.sqrt)

    sigma = ys.rolling(window=w).apply(np.std)

    BB_up = BB_mid + k * sigma
    BB_low = BB_mid - k * sigma

    if (ys[-2] > BB_up[-2] and ys[-1] < BB_up[-1]) or \
            (ys[-2] < BB_low[-2] and ys[-1] < BB_low[-1]):
        signal = -1
    elif (ys[-2] < BB_low[-2] and ys[-1] > BB_low[-1]) or \
            (ys[-2] > BB_up[-2] and ys[-1] > BB_up[-1]):
        signal = 1
    else:
        signal = 0

    dict_results = {
        'Mid': BB_mid,
        'Up': BB_up,
        'Low': BB_low,
        'signal': signal
    }

    return dict_results
"""
my_strategy1.write_py('BollingerBand', x)

######################################################################
# ordinary statistical assessment回测
######################################################################
ordinary_statistical_assessment()

######################################################################
# bootstrap assessment回测
######################################################################
from bootstrap_assessment import BootstrapAssessment
# bootstrap backtest
bootstrap = BootstrapAssessment(symbol='SHFE.rb1905',
                                 start_dt=start_date, end_dt=end_date,
                                 cc=True, strategy=my_strategy1)

######################################################################
# Tianqin Backtesting回测
######################################################################
from my_TqBacktest import TianqinBacktesing
# TqBacktest
symbol = 'SHFE.rb1910'
TianqinBacktesing()

# Construct live_monitoring

"""
construct tianqinbacktest
construct tianqin real-time monitoring
real-time trading
"""


