#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

"""
网格交易策略
参考: https://www.shinnytech.com/blog/grid-trading/
"""

import datetime as dt
from functools import reduce
from contextlib import closing
from tqsdk import TqApi, TargetPosTask, TqSim, TqBacktest, BacktestFinished

# 网格计划参数:
symbol = "DCE.jd1901"  # 合约代码
# api = TqApi(TqSim())
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019,1,2), end_dt=dt.date(2019,3,20)))

quote = api.get_quote(symbol)  # 行情数据
target_pos = TargetPosTask(api, symbol)
target_volume = 0  # 目标持仓手数


async def price_watcher(open_price, close_price, volume):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    global target_volume
    async with api.register_update_notify(quote) as update_chan:  # 当 quote 有更新时会发送通知到 update_chan 上
        while True:
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发开仓条件
                if (volume > 0 and quote["last_price"] <= open_price) or (volume < 0 and quote["last_price"] >= open_price):
                    break
            target_volume += volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote["datetime"], "最新价:", quote["last_price"], "开仓", volume, "手", "总仓位:", target_volume, "手")
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发平仓条件
                if (volume > 0 and quote["last_price"] > close_price) or (volume < 0 and quote["last_price"] < close_price):
                    break
            target_volume -= volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote["datetime"], "最新价:", quote["last_price"], "平仓", volume, "手", "总仓位:", target_volume, "手")


for i in range(grid_amount):
    api.create_task(price_watcher(grid_prices_long[i+1], grid_prices_long[i], grid_volume_long[i]))
    api.create_task(price_watcher(grid_prices_short[i+1], grid_prices_short[i], grid_volume_short[i]))

with closing(api):
    try:
        while True:
            api.wait_update()
    except BacktestFinished:
        print('Backtest end')