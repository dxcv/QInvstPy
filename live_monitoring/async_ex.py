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
    dict_update_quote_chan[SYMBOL] = api.register_update_notify(dict_quotes[SYMBOL])


async def signal_generator(SYMBOL):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    klines = dict_klines[SYMBOL]
    quote = dict_quotes[SYMBOL]
    position = dict_positions[SYMBOL]
    target_pos = dict_target_pos[SYMBOL]
    update_quote_chan = dict_update_quote_chan[SYMBOL]
    update_kline_chan = dict_update_kline_chan[SYMBOL]
    while True:
        async for _ in update_kline_chan:
            target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
            k15 = str(dt.datetime.fromtimestamp(klines.datetime[-2] / 1e9) + pd.Timedelta(minutes=14, seconds=59))
            ys = pd.Series(data=klines.close[-100:-1],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                           )
            dict_results = MACD_adj(ys)
            if target_pos_value == 0 and dict_results['signal'][-1] == 1:
                # 上涨阶段金叉 做多
                target_pos_value = 5
                print(SYMBOL, "上涨阶段做多", '时间：', k15)
                break

            if target_pos_value == 0 and dict_results['signal'][-1] == -1:
                # 下跌阶段死叉，做空
                target_pos_value = -5
                print(SYMBOL, "下跌阶段做空", '时间：', k15)
                break

            if (target_pos_value > 0 and dict_results['HIST'][-2] > 0 and
                (dict_results['HIST'][-1] < dict_results['HIST'][-2])) or \
                    (target_pos_value < 0 and dict_results['HIST'][-2] < 0 and
                     (dict_results['HIST'][-1] > dict_results['HIST'][-2])):
                target_pos_value = 0
                print(SYMBOL, '止损平仓', '时间：', k15)
                break
        print(SYMBOL, '信号时间', k15)
        target_pos.set_target_volume(target_pos_value)

        async for _ in update_quote_chan:
            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 2) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 2):
                target_pos_value = 0

                break
        print(SYMBOL, '止盈平仓', "时间:", quote["datetime"])
        target_pos.set_target_volume(target_pos_value)

    await update_quote_chan.close()
    await update_kline_chan.close()



for symbol in ls_symbols:
    api.create_task(signal_generator(symbol))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('Backtest end')