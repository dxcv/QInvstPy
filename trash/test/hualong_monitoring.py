# -*- coding: utf-8 -*-
"""
@author: chen zhang
"""

import datetime as dt
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from trading_strategies.preprocessing import RW
from trading_strategies.preprocessing import TP
from trading_strategies.preprocessing import PIPs

from trading_strategies.technical_indicators import SMA

from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask

import seaborn as sns
sns.set_style('white')

SYMBOL = 'CFFEX.IF1904'

api = TqApi('SIM')
# api = TqApi(TqSim())#, backtest=TqBacktest(start_dt=dt.date(2019, 2, 13), end_dt=dt.date(2019, 2, 15)))


def wave_plotting(ys, Peaks, Bottoms, **kwargs):
    ls_x = ys.index.tolist()
    num_x = len(ls_x)
    ls_time_ix = np.linspace(0, num_x - 1, num_x)
    ls_p = Peaks.index.tolist()
    ls_b = Bottoms.index.tolist()
    ls_peaks_time = [ys.index.get_loc(x) for x in ls_p]
    ls_bottoms_time = [ys.index.get_loc(x) for x in ls_b]

    # ds_MA = kwargs['MA']

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.plot(ls_time_ix, ys.values)
    # ax.plot(ls_time_ix, ds_MA.values)
    ax.scatter(x=ls_peaks_time, y=Peaks.values, marker='o', color='r', alpha=0.5)
    ax.scatter(x=ls_bottoms_time, y=Bottoms.values, marker='o', color='g', alpha=0.5)

    # for i in ls_peaks_time:
    #     ax.text(x=i, y=Peaks.loc[ls_x[i]],
    #             s=ls_x[i], withdash=True,
    #             )
    new_xticklabels = [ls_x[np.int(i)] for i in list(ax.get_xticks()) if i in ls_time_ix]
    new_xticklabels = [ls_x[0]] + new_xticklabels
    new_xticklabels.append(ls_x[-1])
    ax.set_xticklabels(new_xticklabels)
    for tick in ax.get_xticklabels():
        tick.set_rotation(15)
    #        plt.savefig('1.jpg')
    plt.show()

def get_wave_line(klines, method='RW', **kwargs):
    '''
    计算波浪指标
    :param klines:
    :param method:

    :return:
    '''
    ys = pd.Series(data=klines.close[-100:-1],
                   index=[str(dt.datetime.fromtimestamp(i / 1e9)) for i in klines.datetime[-100:-1]]
                   )

    l = len(ys)
    if method == 'RW':
        Peaks, Bottoms = RW(ys, w=kwargs['w'], iteration=kwargs['iteration'])
        # Peaks, Bottoms = RW(ys, w=3, iteration=0)
    elif method == 'TP':
        Peaks, Bottoms = TP(ys, iteration=kwargs['iteration'])

    ls_ix = ys.index.tolist()
    ls_ix_peaks = Peaks.index.tolist()
    ls_ix_bottoms = Bottoms.index.tolist()
    P_idx_t = [ys.index.get_loc(x) for x in ls_ix_peaks]
    B_idx_t = [ys.index.get_loc(x) for x in ls_ix_bottoms]

    P_idx = pd.Series(index=ls_ix_peaks, data=[1]*len(ls_ix_peaks))
    B_idx = pd.Series(index=ls_ix_bottoms, data=[2]*len(ls_ix_bottoms))
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

    # MA = SMA(ys, w=kwargs['weight_day'])['SMA']
    MA = SMA(ys, w=20)

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


quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, duration_seconds=60)

with closing(api):
    while True:
        api.wait_update()
        if api.is_changing(klines[-1], 'datetime'):
            print(dt.datetime.fromtimestamp(klines.datetime[-1]/1e9))
            ys, pricet, MA, h_up, h_down, Wave_up, Wave_down, ls_up, ls_down = get_wave_line(
                klines, 'RW', w=2, iteration=2, weight_day=20)
            # print(ys)

        """交易规则"""
        if api.is_changing(quote, "last_price"):
            print('最新价：%f' % quote['last_price'])

            # 上升浪一
            if  Y < (Wave_up[1] / Wave_up[0] - 1) < Z:

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


if __name__ == '__main__':
    df_ys = pd.read_csv('./trading_strategies/IF1903_1min.csv')
    df_ys.datetime = df_ys.datetime.apply(pd.to_datetime)
    df_ys.datetime = df_ys.datetime.apply(lambda x: str(x))
    df_ys.set_index('datetime', inplace=True)
    ls_cols = df_ys.columns.tolist()
    str_Close = [i for i in ls_cols if i[-6:] == '.close'][0]
    ys = df_ys.loc[:, str_Close]

    ys = ys[-200:]