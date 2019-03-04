#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import datetime as dt
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY,YEARLY
#from mpl_finance import candlestick_ohlc
#from matplotlib.pylab import date2num

import seaborn as sns
sns.set_style('white')

from preprocessing import RW
from preprocessing import TP
from preprocessing import PIPs
from preprocessing import PB_plotting

from technical_indicators import SMA

from contextlib import closing
import logging
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask


SYMBOL = 'CFFEX.IF1903'
# CLOSE_HOUR, CLOSE_MINUTE = 14, 50

# api = TqApi(TqSim(), backtest=TqBacktest(start_dt=dt.date(2019, 2, 13), end_dt=dt.date(2019, 2, 15)))
api = TqApi('SIM')
# logger = logging.getLogger('HUALONG')
# logger.info('实时监测开始')

klines = api.get_kline_serial(SYMBOL, duration_seconds=60)
quote = api.get_quote(SYMBOL)
position = api.get_position(SYMBOL)
# target_pos = TargetPosTask(api, SYMBOL)
# target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数


def get_wave(klines, method='RW', **kwargs):
    ys = pd.Series(data=klines.close[-40:],
                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-40:]]
                   )
    l = len(ys)
    if method == 'RW':
        Peaks, Bottoms = RW(ys, w=kwargs['w'], iteration=kwargs['iteration'])
        # Peaks, Bottoms = RW(ys, w=1, iteration=2)
    elif method == 'TP':
        Peaks, Bottoms = TP(ys, iteration=kwargs['iteration'])

    ls_p = Peaks.index.tolist()
    ls_b = Bottoms.index.tolist()
    P_idx = [ys.index.get_loc(x) for x in ls_p]
    B_idx = [ys.index.get_loc(x) for x in ls_b]

    P_idx = pd.Series(index=ls_p, data=[1]*len(ls_p))
    B_idx = pd.Series(index=ls_b, data=[2]*len(ls_b))
    PB_idx = P_idx.append(B_idx)
    PB_idx.sort_index(inplace=True)
    m = len(PB_idx.index)

    Pot_Wave_up1 = [2, 1]
    Pot_Wave_down1 = [1, 2]
    Pot_Index = [0] * m

    for i in range(m-1, 0, -1):
        # print(i)
        if PB_idx.iloc[i-1: i+1].values.tolist() == Pot_Wave_up1:
            Pot_Index[i-1] = 1
        elif PB_idx.iloc[i-1: i+1].values.tolist() == Pot_Wave_down1:
            Pot_Index[i-1] = 2

    PNidx = [i for i, x in enumerate(Pot_Index) if x == 1]
    PIidx = [i for i, x in enumerate(Pot_Index) if x == 2]

    Wave_up = ys.loc[(PB_idx.iloc[PNidx[-1]:PNidx[-1]+2]).index.tolist()].copy()
    Wave_down = ys.loc[(PB_idx.iloc[PIidx[-1]:PIidx[-1]+2]).index.tolist()].copy()

    MA = SMA(ys, w=5)['SMA']
    # wave_plotting(ys, Peaks, Bottoms, MA=MA)

    dict_results = {
        'Up': Wave_up,
        'Down': Wave_down,
        'Peaks': Peaks,
        'Bottoms': Bottoms,
        'MA': MA
    }

    Wave_up = dict_results['Up']
    Wave_down = dict_results['Down']
    MA = dict_results['MA']
    ls_up = Wave_up.index.tolist()
    ls_down = Wave_down.index.tolist()

    price0 = ys[0]
    pricet = ys[-1]

    h_up = Wave_up[1] - Wave_up[0]
    h_down = Wave_down[0] - Wave_down[1]

    return ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down


# try:
while True:
    api.wait_update()
    # 判断最后一根K线的时间是否有变化，如果发生变化则表示新产生了一根K线
    if api.is_changing(klines[-1], "datetime"):
        print("新K线", dt.datetime.fromtimestamp(klines[-1]["datetime"]/1e9))
        ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down = \
            get_wave(klines, method='RW', w=2, iteration=0)
        # print(pricet)
        # print(ys)
        # print('last kline close price:', klines.close[-1])

        # 上升浪一
        if Wave_up[0] < pricet < Wave_up[1] and \
            MA.loc[ls_up][0] > Wave_up[0] and MA.loc[ls_up][1] < Wave_up[1] and \
                pricet - MA[-1] < 0.02:
            print('-'*200)
            print('up')
            print('price target: ', pricet+h_up)
            print('stop loss: ', Wave_up[0])
            print('-' * 200)
            # target_pos.set_target_volume(1)

        # 下降浪一
        if Wave_down[0] > pricet > Wave_down[1] and \
            MA.loc[ls_down[0]] < Wave_down[0] and MA.loc[ls_down][1] > Wave_down[1] and \
                MA[-1] - pricet < 0.02:
            print('price target: ', pricet-h_down)
            print('stop loss: ', Wave_down[0])
                # target_pos.set_target_volume(-1)

        # if api.is_changing(quote, "datetime"):
        #     print('last price:', quote['last_price'])
        #     print('time:', quote['datetime'])
        #     if (quote['last_price'] >= pricet+h_up) or (quote['last_price'] < Wave_up[0]) or \
        #             (quote['last_price'] <= pricet - h_down) or (quote['last_price'] > Wave_down[0]):
        #         target_pos.set_target_volume(0)


# except BacktestFinished:  # 回测结束
#     print("----回测结束----")

api.close()