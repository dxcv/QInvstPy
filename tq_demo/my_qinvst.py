# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 14:06:53 2019

@author: chen zhang
"""
#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import date
from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, TargetPosTask

# 在创建 api 实例时传入 TqBacktest 就会进入回测模式
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 5, 10)))
# 获得 m1901 5分钟K线的引用
klines = api.get_kline_serial("DCE.m1901", 15*60, data_length=15)
# # 创建 m1901 的目标持仓 task，该 task 负责调整 m1901 的仓位到指定的目标仓位
# target_pos = TargetPosTask(api, "DCE.m1901")

# 使用with closing机制确保回测完成后释放对应的资源
with closing(api):
    while True:
        api.wait_update()
        if api.is_changing(klines):
            print(klines[-1]['close'])
            print(api.get_account()['balance'])