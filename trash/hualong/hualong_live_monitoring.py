﻿#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chen zhang'

import datetime as dt
from contextlib import closing

import numpy as np
import pandas as pd
from tqsdk import TqApi

from technical_indicators import SMA
# from trading_strategies.technical_indicators import SMA

# import seaborn as sns
# sns.set_style('white')

SYMBOL = 'CFFEX.IF1904'

api = TqApi('SIM')

klines = api.get_kline_serial(SYMBOL, duration_seconds=60)
quote = api.get_quote(SYMBOL)


def wave(klines, w=1, X=20):
    ys = pd.Series(data=klines.close[-100:-1],
                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                   )
    l = len(ys)
    ls_ix = ys.index.tolist()
    ls_ix_peaks = []
    ls_ix_bottoms = []

    for i in range(l-w-1, w-1, -1):
        # print(i)
        if ys.iloc[i] > np.max(ys.iloc[i-w: i]) and \
             ys.iloc[i] > np.max(ys.iloc[i+1: i+w+1]):
            ls_ix_peaks.append(ls_ix[i])
        if ys.iloc[i] < np.min(ys.iloc[i-w: i]) and \
             ys.iloc[i] < np.min(ys.iloc[i+1: i+w+1]):
            ls_ix_bottoms.append(ls_ix[i])
    Peaks = pd.Series(index=ls_ix_peaks, data=ys.loc[ls_ix_peaks])
    Bottoms = pd.Series(index=ls_ix_bottoms, data=ys.loc[ls_ix_bottoms])

    # 横坐标t时序
    ls_time_ix = np.linspace(0, l-1, l)
    P_idx_t = [ys.index.get_loc(x) for x in ls_ix_peaks]
    B_idx_t = [ys.index.get_loc(x) for x in ls_ix_bottoms]

    # 涨1跌2
    P_idx = pd.Series(index=ls_ix_peaks, data=[1]*len(ls_ix_peaks))
    B_idx = pd.Series(index=ls_ix_bottoms, data=[2]*len(ls_ix_bottoms))
    PB_idx = P_idx.append(B_idx)
    PB_idx.sort_index(inplace=True)
    m = len(PB_idx.index)

    #判断最后两个方向
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

    MA = SMA(ys, w=X)['SMA']
    # MA = SMA(ys, w=5)['SMA']

    dict_results = {
        'ys': ys,
        'Up': Wave_up,
        'Down': Wave_down,
        'Peaks': Peaks,
        'Bottoms': Bottoms,
        'MA': MA
    }

    return dict_results


def wave_rule(dict_results, Y=0.0025, Z=0.015):
    ys = dict_results['ys']
    Peaks = dict_results['Peaks']
    Bottoms = dict_results['Bottoms']
    Wave_up = dict_results['Up']
    Wave_down = dict_results['Down']
    MA = dict_results['MA']

    ls_up = Wave_up.index.tolist()
    ls_down = Wave_down.index.tolist()

    # check if there is any Peaks or Bottoms between this definition of Wave
    if Wave_up.index.tolist()[1] == Peaks.index.tolist()[0]:
        pass
    elif Wave_up.index.tolist()[1] == Peaks.index.tolist()[1]:
        Wave_up = Wave_up.drop(Wave_up.index.tolist()[1])
        Wave_up = Wave_up.append(
            ys.iloc[ys.index.get_loc(Peaks.index.tolist()[0]):ys.index.get_loc(Peaks.index.tolist()[0])+1])

    if Wave_down.index.tolist()[1] == Bottoms.index.tolist()[0]:
        pass
    elif Wave_down.index.tolist()[1] == Bottoms.index.tolist()[1]:
        Wave_down = Wave_down.drop(Wave_down.index.tolist()[1])
        Wave_down = Wave_down.append(
            ys.iloc[ys.index.get_loc(Bottoms.index.tolist()[0]):ys.index.get_loc(Bottoms.index.tolist()[0]) + 1])

    pricet = ys[-1]
    stop_loss = np.nan
    target_price = np.nan

    h_up = Wave_up[1] - Wave_up[0]
    h_down = Wave_down[0] - Wave_down[1]

    if (Y < (Wave_up[1] / Wave_up[0] - 1) < Z) and \
            (Wave_up[0] < MA.loc[ls_up[0]] < MA.loc[ls_up[1]] < MA[-1]) and \
            (np.abs(pricet - MA[-1]) < 0.6):
        signal = 1
        stop_loss = Wave_up[0]
        target_price = pricet + h_up
    elif (-Z < (Wave_down[1] / Wave_down[0] - 1) < -Y) and \
            (Wave_down[0] > MA.loc[ls_down[0]] > MA.loc[ls_down[1]] > MA[-1]) and \
            (np.abs(pricet - MA[-1]) < 0.6):
        signal = -1
        stop_loss = Wave_down[0]
        target_price = pricet - h_down
    else:
        signal = 0

    return Wave_up, Wave_down, signal, stop_loss, target_price


with closing(api):
    while True:
        api.wait_update()
        # 判断最后一根K线的时间是否有变化，如果发生变化则表示新产生了一根K线
        if api.is_changing(klines[-1], "datetime"):
            # 注意引用k线的时间是k线的起始时间
            k_time = dt.datetime.fromtimestamp(klines[-2]["datetime"]/1e9)
            dict_results = wave(klines, w=3, X=20)
            Wave_up, Wave_down, signal, stop_loss, target_price = wave_rule(dict_results)
            print(k_time)
            if signal == 1:
                print('开仓多头')
                print("判断信号K线时间", k_time)
                print(Wave_up)
                print('price target: ', target_price)
                print('stop loss: ', stop_loss)
            elif signal == -1:
                print('开仓空头')
                print("判断信号K线时间", k_time)
                print(Wave_down)
                print('price target: ', target_price)
                print('stop loss: ', stop_loss)


# if __name__ == '__main__':
#
    # df_ys = pd.read_csv('./tools/IF1904_1min.csv')
    # df_ys.datetime = df_ys.datetime.apply(pd.to_datetime)
    # df_ys.datetime = df_ys.datetime.apply(lambda x: str(x))
    # df_ys.set_index('datetime',inplace=True)
    # ls_cols = df_ys.columns.tolist()
    # str_Close = [i for i in ls_cols if i[-6:] == '.close'][0]
    # ys = df_ys.loc[:, str_Close]
