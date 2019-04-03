#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import datetime as dt
import numpy as np
import pandas as pd

from trading_strategies.technical_indicators import MACD_adj

from contextlib import closing
from tqsdk import TqApi, TargetPosTask, TqSim, TqBacktest, BacktestFinished

# 合约代码准备
ls_symbols = ['SHFE.rb1905', 'SHFE.hc1905']
# SYMBOL = "DCE.i1905"  # 合约代码
# api = TqApi(TqSim())
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,1,10)))

dict_quotes = {}
dict_klines = {}
dict_positions = {}
dict_target_pos = {}
dict_update_kline_chan = {}
dict_update_quote_chan = {}

for SYMBOL in ls_symbols:
    dict_quotes[SYMBOL] = api.get_quote(SYMBOL)  # 行情数据
    dict_klines[SYMBOL] = api.get_kline_serial(SYMBOL, duration_seconds=15 * 60)
    dict_positions[SYMBOL] = api.get_position(SYMBOL)
    dict_target_pos[SYMBOL] = TargetPosTask(api, SYMBOL)
    dict_update_kline_chan[SYMBOL] = api.register_update_notify(dict_klines[SYMBOL])
    # dict_update_quote_chan[SYMBOL] = api.register_update_notify(dict_quotes[SYMBOL])


async def signal_generator(SYMBOL):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    klines = dict_klines[SYMBOL]
    quote = dict_quotes[SYMBOL]
    position = dict_positions[SYMBOL]
    target_pos = dict_target_pos[SYMBOL]
    # update_quote_chan = dict_update_quote_chan[SYMBOL]
    update_kline_chan = dict_update_kline_chan[SYMBOL]
    while True:
        async for _ in update_kline_chan:
            k15 = str(dt.datetime.fromtimestamp(klines.datetime[-2] / 1e9) + pd.Timedelta(minutes=14, seconds=59))
            ys = pd.Series(data=klines.close[-100:-1],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                           )
            print(SYMBOL, k15)
    await update_kline_chan.close()




async def signal_generator2(SYMBOL):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    klines = dict_klines[SYMBOL]
    quote = dict_quotes[SYMBOL]
    position = dict_positions[SYMBOL]
    target_pos = dict_target_pos[SYMBOL]
    # update_quote_chan = dict_update_quote_chan[SYMBOL]
    # update_kline_chan = dict_update_kline_chan[SYMBOL]
    async with dict_update_kline_chan[SYMBOL] as update_kline_chan:
        while True:
            async for _ in update_kline_chan:
                k15 = str(dt.datetime.fromtimestamp(klines.datetime[-2] / 1e9) + pd.Timedelta(minutes=14, seconds=59))
                ys = pd.Series(data=klines.close[-100:-1],
                               index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                               )
                print(SYMBOL, '信号时间', k15)

for symbol in ls_symbols:
    api.create_task(signal_generator2(symbol))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('Backtest end')