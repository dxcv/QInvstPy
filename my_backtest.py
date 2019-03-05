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


######################################################################
# 策略编写与导入
######################################################################
my_strategy1 = my_strategy()
'''
what analysis is used 
idea from XXX paper
'''

######################################################################
# bootstrap assessment回测
######################################################################
from bootstrap_assessment import bootstrap_assessment
# bootstrap backtest
bootstrap = bootstrap_assessment(symbol='SHFE.rb1905',
                                 start_dt=start_date, end_dt=end_date,
                                 cc=True, strategy=my_strategy1)

######################################################################
# Tianqin Backtesting回测
######################################################################
from my_TqBacktest import TianqinBacktesing
# TqBacktest
symbol = 'SHFE.rb1810'
TianqinBacktesing()

# Construct live_monitoring

"""
construct tianqinbacktest
construct tianqin real-time monitoring
real-time trading
"""

if __name__ == '__main__':
    from trading_strategies.technical_indicators import SMA

    symbol = 'SHFE.rb1905'
    duration_seconds = 10
    # api = TqApi('SIM', url='ws://192.168.1.6:7777', backtest=TqBacktest(start_dt=dt.date(2019,2,13), end_dt=dt.date(2019,2,14)))
    api = TqApi('SIM')#, backtest=TqBacktest(start_dt=dt.date(2019, 2, 13), end_dt=dt.date(2019, 2, 14)))
    quote = api.get_quote(symbol)
    klines = api.get_kline_serial(symbol, duration_seconds=duration_seconds)  #
    target_pos = TargetPosTask(api, symbol)

    with closing(api):
        try:
            while True:
                api.wait_update()
                if api.is_changing(klines):
                    try:
                        now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")  # 当前quote的时间
                    except:
                        now = 'No data'
                    print(now)
                    ys = pd.Series(data=klines.close[-50:],
                                   index=[dt.datetime.fromtimestamp(i/1e9) for i in klines.datetime[-50:]]
                                   )
                    if SMA(ys, 20) == 1:  # 如果预测结果为涨: 买入
                        print(quote["datetime"], "预测下一交易日为 涨")
                        target_pos.set_target_volume(1)
                    elif SMA(ys, 20) == -1:
                        print(quote["datetime"], "预测下一交易日为 跌")
                        target_pos.set_target_volume(-1)
                    else:
                        print(quote["datetime"], "meiyoufangxiang pingcang")
                        target_pos.set_target_volume(0)
        except BacktestFinished:  # 回测结束, 获取预测结果，统计正确率
            print("----回测结束----")


