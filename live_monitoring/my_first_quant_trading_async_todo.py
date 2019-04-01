#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt
import time

import logging
import asyncio

from contextlib import closing
from tqsdk import TqApi, TqSim, TqAccount, TqBacktest, BacktestFinished, TargetPosTask

from trading_strategies.technical_indicators import MACD_adj

# api = TqApi('SIM')
# 实盘跟踪
# api = TqApi(TqAccount(args.broker, args.user_name, args.password))
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,1,10)))

# 合约代码准备
ls_symbols = ['SHFE.rb1910', 'SHFE.hc1910', 'CZCE.MA909', 'CZCE.TA909']

account = api.get_account()
strategy = MACD_adj


async def signal_generator(SYMBOL, strategy):
    """该task应用策略在价格触发时开仓，出发平仓条件时平仓"""
    klines = api.get_kline_serial(SYMBOL, duration_seconds=15*60)
    position = api.get_position(SYMBOL)
    target_pos = TargetPosTask(api, SYMBOL)

    async with api.register_update_notify(klines) as update_klines_chan:
        while True:
            async for _ in update_klines_chan:
                k15 = str(dt.datetime.fromtimestamp(klines.datetime[-1] / 1e9))
                print(SYMBOL, '信号时间', k15)

                ys = pd.Series(data=klines.close[-100:-1],
                               index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                               )
                dict_results = strategy(ys)
                # print(SYMBOL, 'HIST', (dict_results['HIST'][-2], dict_results['HIST'][-1]))
                target_pos_value = position['volume_long'] - position['volume_short']

                if target_pos_value == 0:
                    # 上涨阶段金叉 做多
                    if dict_results['signal'][-1] == 1:
                        target_pos_value = 5
                        target_pos.set_target_volume(target_pos_value)
                        print(SYMBOL, "上涨阶段做多", '时间：', k15)
                    # 下跌阶段死叉，做空
                    if dict_results['signal'][-1] == -1:
                        target_pos_value = -5
                        target_pos.set_target_volume(target_pos_value)
                        print(SYMBOL, "下跌阶段做空", '时间：', k15)
                    break

                if (target_pos_value > 0 and dict_results['HIST'][-2] > 0 and
                    (dict_results['HIST'][-1] < dict_results['HIST'][-2])) or \
                        (target_pos_value < 0 and dict_results['HIST'][-2] < 0 and
                         (dict_results['HIST'][-1] > dict_results['HIST'][-2])):
                    target_pos.set_target_volume(0)
                    print(SYMBOL, '止损平仓', '时间：', k15)
                    break


async def close_win(SYMBOL):
    """该task应用策略在价格触发止盈条件时平仓"""
    quote = api.get_quote(SYMBOL)
    position = api.get_position(SYMBOL)
    target_pos = TargetPosTask(api, SYMBOL)

    async with api.register_update_notify(quote) as update_quote_chan:
        while True:
            async for _ in update_quote_chan:
                target_pos = TargetPosTask(api, SYMBOL)
                target_pos_value = position['volume_long'] - position['volume_short']
                print(SYMBOL, target_pos_value, "时间:", quote["datetime"])
                if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 2) or \
                        (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 2):
                    target_pos.set_target_volume(0)
                    print(SYMBOL, '止盈平仓')
                    break

for symbol in ls_symbols:
    api.create_task(signal_generator(symbol, MACD_adj))
    api.create_task(close_win(symbol))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('----回测结束----')

