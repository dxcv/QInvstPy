#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt
import time

from contextlib import closing
import argparse
from tqsdk import TqApi, TqSim, TqAccount, TargetPosTask, InsertOrderUntilAllTradedTask

from trading_strategies.technical_indicators import MACD_adj

#解析命令行参数
parser = argparse.ArgumentParser()
# parser.add_argument('--broker')
# parser.add_argument('--user_name')
# parser.add_argument('--password')


api = TqApi('SIM')
# 实盘跟踪
# api = TqApi(TqAccount(args.broker, args.user_name, args.password))

# 合约代码准备
ls_symbols = ['SHFE.rb1910', 'SHFE.hc1910', 'CZCE.MA1909', 'CZCE.TA909']

dict_quotes = {}
dict_klines = {}
dict_positions = {}
dict_target_pos = {}
dict_target_pos_value = {}

for SYMBOL in ls_symbols:
    dict_quotes[SYMBOL] = api.get_quote(SYMBOL)
    dict_klines[SYMBOL] = api.get_kline_serial(SYMBOL, duration_sections=15*60)
    dict_positions[SYMBOL] = api.get_position(SYMBOL)
    dict_target_pos[SYMBOL] = TargetPosTask(api, SYMBOL)
    dict_target_pos_value[SYMBOL] = target_pos_value

CLOSE_HOUR, CLOSE_MINUTE = 14, 55  # 平仓时间

account = api.get_account()

with closing(api):
    while True:
        for SYMBOL in ls_symbols:
            xyz(SYMBOL)
            target_pos.set_target_volume(target_pos_value)
        api.wait_update()
        for SYMBOL in ls_symbols:
            xyz(SYMBOL)
        if api.is_changing(klines[-1], 'datetime'):
            # 等待新的K线生成
            api.wait_update()
            k15 = str(dt.datetime.fromtimestamp(klines.datetime[-1] / 1e9))
            print('信号时间', k15)

            ys = pd.Series(data=klines.close[-300:-1],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-300:-1]]
                           )
            # print(ys)
            dict_results = MACD_adj(ys)
            print('diff', dict_results['MACD'][-1])
            print('SL', dict_results['SL'][-1])
            print('HIST', (dict_results['HIST'][-2], dict_results['HIST'][-1]))

            if target_pos_value == 0:
                # 上涨阶段金叉 做多
                if dict_results['signal'][-1] == 1:
                    target_pos_value = 5
                    print("上涨阶段金叉 做多")
                # 下跌阶段死叉，做空
                if dict_results['signal'][-1] == -1:
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
            # print('行情最新时间', quote_now)
            # TODO: 根据不同合约参数调整止盈价格 很重要！
            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 2) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 2):
                target_pos_value = 0
                print('止盈平仓')

            if target_pos_value > 0:
                print('多头开仓价', position["open_price_long"])
                print('最新价', quote['last_price'])

            if target_pos_value < 0:
                print('空头开仓价', position["open_price_short"])
                print('最新价', quote['last_price'])
