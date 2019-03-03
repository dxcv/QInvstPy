import numpy as np
import pandas as pd


def SMA(ys, k):
    """

    :param ys: column vector of price series with str time index
    :param k: lag number
    :return signal: 1, -1 or 0
    """
    SMA = ys.rolling(window=k).apply(np.mean)
    if ys[-1] > SMA[-1] and ys[-2] < SMA[-2]:
        signal = 1
    elif ys[-1] < SMA[-1] and ys[-2] > SMA[-2]:
        signal = -1
    else:
        signal = 0
    return signal
