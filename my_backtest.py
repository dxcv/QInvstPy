#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import os

import numpy as np
import pandas as pd
import datetime as dt

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

from asset_selection import my_asset_selection

pd.set_option('display.max_rows', None)  # 设置Pandas显示的行数
pd.set_option('display.width', None)  # 设置Pandas显示的宽度

'''
what analysis is used 
idea from XXX paper
'''

"""
select asset
select_symbol: according to the most traded/OI contract
select_time_interval: 5min 15min 1d
based on the trading break: 10:15-10:29, hard to tune time interval

select_backtest_period
construct bootstrap backtest

construct tianqinbacktest
construct tianqin real-time monitoring
real-time trading

"""

# 确定交易品种和合约
ls_assets = my_asset_selection()
ls_assets = ['rb']

ls_symbols = ['SHFE.rb1901', 'SHFE.ru1811']

symbol = "SHFE.ru1811"  # 交易合约代码

# TODO: 交易规则 不同品种不一样。。
close_hour, close_minute = 14, 54  # 预定收盘时间(因为真实收盘后无法进行交易, 所以提前设定收盘时间)
close_hour, close_minute = 10, 14
close_hour, close_minute = 23, 0
close_hour, close_minute = 23, 30
duration_seconds = 5 * 60
duration_seconds = 15 * 60



api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2018, 7, 2), end_dt=dt.date(2018, 7, 26)))
quote = api.get_quote(symbol)
klines = api.get_kline_serial(symbol, duration_seconds=24 * 60 * 60)  # 日线
target_pos = TargetPosTask(api, symbol)
with closing(api):
    try:
        while True:
            while not api.is_changing(klines[-1], "datetime"):  # 等到达下一个交易日
                api.wait_update()
            while True:
                api.wait_update()
                # 在收盘后预测下一交易日的涨跌情况
                if api.is_changing(quote, "datetime"):
                    now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")  # 当前quote的时间
                    # 判断是否到达预定收盘时间: 如果到达 则认为本交易日收盘, 此时预测下一交易日的涨跌情况, 并调整为对应仓位
                    if now.hour == close_hour and now.minute >= close_minute:
                        # 1- 获取数据
                        x_train, y_train, x_predict = get_prediction_data(klines, 75)  # 参数1: K线, 参数2:需要的数据长度

                        # 2- 利用机器学习算法预测下一个交易日的涨跌情况
                        # n_estimators 参数: 选择森林里（决策）树的数目; bootstrap 参数: 选择建立决策树时，是否使用有放回抽样
                        clf = RandomForestClassifier(n_estimators=30, bootstrap=True)
                        clf.fit(x_train, y_train)  # 传入训练数据, 进行参数训练
                        predictions.append(bool(clf.predict([x_predict])))  # 传入测试数据进行预测, 得到预测的结果

                        # 3- 进行交易
                        if predictions[-1] == True:  # 如果预测结果为涨: 买入
                            print(quote["datetime"], "预测下一交易日为 涨")
                            target_pos.set_target_volume(10)
                        else:  # 如果预测结果为跌: 卖出
                            print(quote["datetime"], "预测下一交易日为 跌")
                            target_pos.set_target_volume(-10)
                        break

    except BacktestFinished:  # 回测结束, 获取预测结果，统计正确率
        df_klines = klines.to_dataframe()  # 将K线序列中的数据转换为 pandas.DataFrame
        df_klines["pre_close"] = df_klines["close"].shift(1)  # 增加 pre_close(上一交易日的收盘价) 字段
        df_klines = df_klines[-len(predictions) + 1:]  # 取出在回测日期内的K线数据
        df_klines["prediction"] = predictions[:-1]  # 增加预测的本交易日涨跌情况字段(向后移一个数据目的: 将 本交易日对应下一交易日的涨跌 调整为 本交易日对应本交易日的涨跌)
        results = (df_klines["close"] - df_klines["pre_close"] >= 0) == df_klines["prediction"]

        print(df_klines)
        print("----回测结束----")
        print("预测结果正误:\n", results)
        print("预测结果数目统计: 总计", len(results),"个预测结果")
        print(pd.value_counts(results))
        print("预测的准确率:")
        print((pd.value_counts(results)[True]) / len(results))