#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

from trading_selection import my_assets_selection
from trading_selection import symbols_selection
from bootstrap_assessment import bootstrap_assessment
from my_TqBacktest import TianqinBacktesing

pd.set_option('display.max_rows', None)  # 设置Pandas显示的行数
pd.set_option('display.width', None)  # 设置Pandas显示的宽度

'''
what analysis is used 
idea from XXX paper
'''

"""
construct tianqinbacktest
construct tianqin real-time monitoring
real-time trading

"""

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

#
#
# TODO: 交易规则 不同品种不一样。。
# eg., rb
long_asset = ls_long_assets[0]
close_hour_day, close_minute_day = 14, 54  # 预定收盘时间(因为真实收盘后无法进行交易, 所以提前设定收盘时间)
# close_hour, close_minute = 10, 14
close_hour_night, close_minute_night = 22, 56
# close_hour, close_minute = 23, 30

# set time interval
# say 5分钟K线
# select_time_interval: 5min 15min 1d
# based on the trading break: 10:15-10:29, hard to adjust time interval
duration_seconds = 5 * 60
# duration_seconds = 15 * 60
duration_seconds = 24*60*60

# backtest period
start_date = dt.date(2018, 7, 2)
end_date = dt.date(2018, 7, 26)

# bootstrap backtest
bootstrap = bootstrap_assessment()

# TqBacktest
symbol = 'SHFE.rb1810'
TianqinBacktesing()

# Construct live_monitoring