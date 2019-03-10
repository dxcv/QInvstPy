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

from trading_strategies.technical_indicators import BB

#解析命令行参数
parser = argparse.ArgumentParser()
# parser.add_argument('--broker')
# parser.add_argument('--user_name')
# parser.add_argument('--password')
parser.add_argument('--symbol')
args = parser.parse_args()
print("合约代码参数为: ",  args.symbol) #args.user_name

api = TqApi('SIM')
# 实盘跟踪
# api = TqApi(TqAccount(args.broker, args.user_name, args.password))

SYMBOL = args.symbol
CLOSE_HOUR, CLOSE_MINUTE = 14, 50  # 平仓时间

quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, duration_seconds=15*60)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
# target_pos = InsertOrderUntilAllTradedTask(api, SYMBOL)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数

account = api.get_account()

with closing(api):
    while True:
        print('本机时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        target_pos.set_target_volume(target_pos_value)
        api.wait_update()
        if api.is_changing(klines[-1], 'datetime'):
            # 等待新的K线生成
            api.wait_update()
            k15 = str(dt.datetime.fromtimestamp(klines.datetime[-1] / 1e9))
            print('信号时间', k15)

            ys = pd.Series(data=klines.close[-40:],
                           index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-40:]]
                           )
            dict_results = BB(ys)
            print('Up', dict_results['Up'][-1])
            print('Mid', dict_results['Mid'][-1])
            print('Low', dict_results['Low'][-1])

            if target_pos_value == 0:
                # 上穿下轨 做多
                if dict_results['signal'] == 1:
                    target_pos_value = 5
                    print("上穿下轨 做多")
                # 下穿上轨，做空
                if dict_results['signal'] == -1:
                    target_pos_value = -5
                    print("下穿上轨，做空")

            # if (target_pos_value > 0 and dict_results['HIST'][-2] > 0 and
            #     (dict_results['HIST'][-1] < dict_results['HIST'][-2])) or \
            #         (target_pos_value < 0 and dict_results['HIST'][-2] < 0 and
            #          (dict_results['HIST'][-1] > dict_results['HIST'][-2])):
            #     target_pos_value = 0
            #     print('止损平仓')

        if api.is_changing(quote, 'datetime'):
            quote_now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
            print('行情最新时间', quote_now)
            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] >= 6) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) >= 6):
                target_pos_value = 0
                print('止盈平仓')

            if (target_pos_value > 0 and quote["last_price"] - position["open_price_long"] <= -2) or\
                    (target_pos_value < 0 and (position["open_price_short"] - quote["last_price"]) <= -2):
                target_pos_value = 0
                print('止损平仓')

            # if target_pos_value > 0:
            #     print('多头开仓价', position["open_price_long"])
            #     print('最新价', quote['last_price'])
            #
            # if target_pos_value < 0:
            #     print('空头开仓价', position["open_price_short"])
            #     print('最新价', quote['last_price'])
