#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt

from multiprocessing import Pool

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

from trading_strategies.technical_indicators import MACD_adj


def run_strategy(symbol):
    print('child process ({}) and parent is {}'.format(os.getpid(), os.getppid()))
    print('This is first strategy for symbol: ', symbol)
    quote = api.get_quote(symbol)
    klines = api.get_kline_serial(symbol, duration_seconds=15 * 60)
    position = api.get_position(symbol)
    target_pos = TargetPosTask(api, symbol)
    target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数

    with closing(api):
        try:
            while True:
                target_pos.set_target_volume(target_pos_value)
                api.wait_update()
                if api.is_changing(klines[-1], 'datetime'):
                    # 等待新的K线生成
                    api.wait_update()
                    k15 = str(dt.datetime.fromtimestamp(klines.datetime[-1] / 1e9))
                    print('信号时间', k15)

                    ys = pd.Series(data=klines.close[-100:-1],
                                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                                   )
                    # print(ys)
                    dict_results = MACD_adj(ys)
                    print('diff', dict_results['MACD'][-1])
                    print('SL', dict_results['SL'][-1])
                    print('HIST', (dict_results['HIST'][-2], dict_results['HIST'][-1]))

                    if target_pos_value == 0:
                        # 上涨阶段金叉 做多
                        if dict_results['signal'] == 1:
                            target_pos_value = 5
                            print("上涨阶段金叉 做多")
                        # 下跌阶段死叉，做空
                        if dict_results['signal'] == -1:
                            target_pos_value = -5
                            print("下跌阶段死叉，做空")

                    if (target_pos_value > 0 and dict_results['HIST'][-2] > 0 and
                        (dict_results['HIST'][-1] < dict_results['HIST'][-2])) or \
                            (target_pos_value < 0 and dict_results['HIST'][-2] < 0 and
                             (dict_results['HIST'][-1] > dict_results['HIST'][-2])):
                        target_pos_value = 0
                        print('止损平仓')

                if api.is_changing(quote, 'datetime'):
                    quote_now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
                    print('行情最新时间', quote_now)
                    # TODO: 根据不同合约参数调整止盈价格 很重要！
                    if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 2) or \
                            (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 2):
                        target_pos_value = 0
                        print('止盈平仓')
        except BacktestFinished:
            print('----回测结束----')


if __name__ == '__main__':
    print('Parent process {}'.format(os.getppid()))
    ls_symbols = ['SHFE.rb1905', 'SHFE.hc1905', 'CZCE.MA909', 'CZCE.TA909']
    api = TqApi('SIM', backtest=TqBacktest(start_dt=dt.date(2019, 1, 2), end_dt=dt.date(2019, 1, 10)))
    p = Pool(3)
    for symbol in ls_symbols:
        p.apply_async(run_strategy, args=(symbol,))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')
