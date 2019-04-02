#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import datetime as dt
import numpy as np
import pandas as pd

from trading_strategies.technical_indicators import MACD_adj

from contextlib import closing
from tqsdk import TqApi, TargetPosTask, TqSim, TqBacktest, BacktestFinished

# 网格计划参数:
SYMBOL = "DCE.i1905"  # 合约代码
# api = TqApi(TqSim())
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,1,10)))
quote = api.get_quote(SYMBOL)  # 行情数据
klines = api.get_kline_serial(SYMBOL, duration_seconds=15 * 60)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)


async def signal_generator(SYMBOL):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    target_pos_value = 0
    update_kline_chan = api.register_update_notify(klines)
    while True:
        async for _ in update_kline_chan:
            pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
            k15 = str(dt.datetime.fromtimestamp(klines.datetime[-2] / 1e9) + pd.Timedelta(minutes=14, seconds=59))
            print('信号时间', k15)

            ys = pd.Series(data=klines.close[-100:-1],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                           )
            dict_results = MACD_adj(ys)

            if pos_value == 0 and dict_results['signal'][-1] == 1:
                # 上涨阶段金叉 做多
                target_pos_value = 5
                print(SYMBOL, "上涨阶段做多", '时间：', k15)
                break

            if pos_value == 0 and dict_results['signal'][-1] == -1:
                # 下跌阶段死叉，做空
                target_pos_value = -5
                print(SYMBOL, "下跌阶段做空", '时间：', k15)
                break

            if (pos_value > 0 and dict_results['HIST'][-2] > 0 and
                (dict_results['HIST'][-1] < dict_results['HIST'][-2])) or \
                    (pos_value < 0 and dict_results['HIST'][-2] < 0 and
                     (dict_results['HIST'][-1] > dict_results['HIST'][-2])):
                target_pos_value = 0
                print(SYMBOL, '止损平仓', '时间：', k15)
                break
        target_pos.set_target_volume(target_pos_value)

    await update_kline_chan.close()


async def close_win(SYMBOL):
    update_quote_chan = api.register_update_notify(quote)  # 当 quote 有更新时会发送通知到 update_chan 上
    while True:
        async for _ in update_quote_chan:
            target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 1) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 1):
                target_pos_value = 0
                print('止盈平仓')
                break
        target_pos.set_target_volume(target_pos_value)

    await update_quote_chan.close()


api.create_task(signal_generator(SYMBOL))
api.create_task(close_win(SYMBOL))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('Backtest end')