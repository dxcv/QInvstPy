#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chenzhang'

import pandas as pd
import datetime as dt
from contextlib import closing
from tqsdk import TqApi, TargetPosTask, TqSim, TqBacktest, BacktestFinished

# 网格计划参数:
# symbol = "DCE.i1905"
ls_symbol = ['DCE.i1905', 'SHFE.rb1905']

api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,1,20)))




async def price_watcher(SYMBOL):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    klines = api.get_kline_serial(SYMBOL, duration_seconds=5 * 60)
    target_pos = TargetPosTask(api, SYMBOL)
    async with api.register_update_notify(klines) as update_price_chan:  # 当 quote 有更新时会发送通知到 update_chan 上
        while True:
            async for _ in update_price_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发开仓条件
                ys = pd.Series(data=klines.close[-100:-1],
                               index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                               )
                target_pos.set_target_volume(1)
                print(SYMBOL, '价格')


async def position_watcher(SYMBOL):
    quote = api.get_quote(SYMBOL)
    position = api.get_position(SYMBOL)
    async with api.register_update_notify(quote) as update_quote_chan:
        while True:
            async for _ in update_quote_chan:
                pos = position['volume_long'] - position['volume_short']

                print(SYMBOL, '持仓', pos)

for symbol in ls_symbol:
    api.create_task(price_watcher(symbol))
    api.create_task(position_watcher(symbol))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('Backtest end')