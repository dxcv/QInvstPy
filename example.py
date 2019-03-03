#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqSim
import pandas as pd
import datetime as dt

api = TqApi(TqSim())
# # 获得cu1812 tick序列的引用
# ticks = api.get_tick_serial("SHFE.cu1812")
# 获得cu1812 10秒K线的引用
klines = api.get_kline_serial("CFFEX.IF1903", duration_seconds=5*60)

def get_index(klines):
    ys = pd.Series(data=klines.close[-40:],
                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-40:]]
                   )
    return ys

while True:
    api.wait_update()
    # 判断最后一根K线的时间是否有变化，如果发生变化则表示新产生了一根K线
    if api.is_changing(klines[-1], "datetime"):
        # datetime: 自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        print("新K线", dt.datetime.fromtimestamp(klines[-1]["datetime"]/1e9))
        print('测试')
        y = klines.datetime[-30:]
        print([str(dt.datetime.fromtimestamp(i/1e9)) for i in klines.datetime[-40:]])
        ys = get_index(klines)
        print(ys)
    # # 判断最后一根K线的收盘价是否有变化
    # if api.is_changing(klines[-1], "close"):
    #     # klines.close返回收盘价序列
    #     print("K线变化", dt.datetime.fromtimestamp(klines[-1]["datetime"]/1e9), klines.close[-1])