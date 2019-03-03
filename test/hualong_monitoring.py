# -*- coding: utf-8 -*-
"""
@author: chen zhang
"""

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
CLOSE_HOUR, CLOSE_MINUTE = 14, 50


# api = TqApi('SIM')
api = TqApi(TqSim())#, backtest=TqBacktest(start_dt=dt.date(2019, 2, 13), end_dt=dt.date(2019, 2, 15)))
logger = logging.getLogger('HUALONG')
logger.info('实时监测开始')


# def wave_plotting(ys, Peaks, Bottoms, **kwargs):
#     ls_x = ys.index.tolist()
#     num_x = len(ls_x)
#     ls_time_ix = np.linspace(0, num_x - 1, num_x)
#     ls_p = Peaks.index.tolist()
#     ls_b = Bottoms.index.tolist()
#     ls_peaks_time = [ys.index.get_loc(x) for x in ls_p]
#     ls_bottoms_time = [ys.index.get_loc(x) for x in ls_b]
#
#     ds_MA = kwargs['MA']
#
#     fig, ax = plt.subplots(1, 1, figsize=(12, 8))
#     ax.plot(ls_time_ix, ys.values)
#     ax.plot(ls_time_ix, ds_MA.values)
#     ax.scatter(x=ls_peaks_time, y=Peaks.values, marker='o', color='r', alpha=0.5)
#     ax.scatter(x=ls_bottoms_time, y=Bottoms.values, marker='o', color='g', alpha=0.5)
#
#     # for i in ls_peaks_time:
#     #     ax.text(x=i, y=Peaks.loc[ls_x[i]],
#     #             s=ls_x[i], withdash=True,
#     #             )
#     new_xticklabels = [ls_x[np.int(i)] for i in list(ax.get_xticks()) if i in ls_time_ix]
#     new_xticklabels = [ls_x[0]] + new_xticklabels
#     new_xticklabels.append(ls_x[-1])
#     ax.set_xticklabels(new_xticklabels)
#     for tick in ax.get_xticklabels():
#         tick.set_rotation(15)
#     #        plt.savefig('1.jpg')
#     plt.ion()
#     plt.pause(5)
#     plt.close()


def get_wave_line(klines, method='RW', **kwargs):
    '''
    计算波浪指标
    :param klines:
    :param method:

    :return:
    '''
    ys = pd.Series(data=klines.close[-40:],
                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-40:]]
                   )

    l = len(ys)
    if method == 'RW':
        Peaks, Bottoms = RW(ys, w=kwargs['w'], iteration=kwargs['iteration'])
        # Peaks, Bottoms = RW(ys, w=1, iteration=2)
    elif method == 'TP':
        Peaks, Bottoms = TP(ys, iteration=kwargs['iteration'])
    #
    ls_x = ys.index.tolist()
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
    #
    # # logger.info('计算上升浪第一浪的低点和高点 最新K线的')

    return ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down


quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, duration_seconds=60*5)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价
# ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down = get_wave_line(klines, 'RW', w=2, iteration=2)

with closing(api):
    try:
        while True:
            api.wait_update()
            if api.is_changing(klines[-1], 'datetime'):
                print(dt.datetime.fromtimestamp(klines.datetime[-1]/1e9))
                ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down = get_wave_line(klines, 'RW', w=2, iteration=2)
                # print(ys)

            # if api.is_changing(quote, "datetime"):
            #     now = dt.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
            #     if now.hour == CLOSE_HOUR and now.minute >= CLOSE_MINUTE:  # 到达平仓时间: 平仓
            #         logger.info("临近本交易日收盘: 平仓")
            #         target_pos.set_target_volume(0)  # 平仓
            #         deadline = time.time() + 60
            #         while api.wait_update(deadline=deadline):  # 等待60秒
            #             pass
            #         api.close()
            #         break

            """交易规则"""
            if api.is_changing(quote, "last price"):
                logger.info('最新价：%f' % quote['last price'])

                # 上升浪一
                if Wave_up[0] < pricet < Wave_up[1] and \
                    MA.loc[ls_up][0] > Wave_up[0] and MA.loc[ls_up][1] < Wave_up[1] and \
                    pricet - MA[-1] < 0.02:
                    logger.info('主升浪一产生，回落至5日均线后开仓做多')
                    print('price target: ', pricet+h_up)
                    print('stop loss: ', Wave_up[0])
                    target_pos_value = 1

                if (target_pos_value > 0 and quote['last price'] > pricet+h_up) or \
                    (target_pos_value > 0 and quote['last price'] < Wave_up[0]):
                    target_pos_value = 0


                # 下降浪一
                if Wave_down[0] > pricet > Wave_down[1] and \
                    MA.loc[ls_down[0]] < Wave_down[0] and MA.loc[ls_down][1] > Wave_down[1] and \
                    MA[-1] - pricet < 0.02:
                    logger.info('主降浪一产生，涨至5日均线后开仓做空')
                    print('price target: ', pricet-h_down)
                    print('stop loss: ', Wave_down[0])
                    target_pos_value = -1

                if (target_pos_value < 0 and quote['last price'] > pricet-h_down) or \
                    (target_pos_value < 0 and quote['last price'] < Wave_down[0]):
                    target_pos_value = 0

    except BacktestFinished:  # 回测结束
        print("----回测结束----")
