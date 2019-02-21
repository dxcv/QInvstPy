
import os
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
select asset
select_symbol: according to the most traded/OI contract
"""


def my_assets_selection():
    """
    +-为多空方向？加入基本面信息？
    :return:
    """
    dict_assets = {
        'long': ['rb'],
        'short': ['MA']
    }
    return dict_assets


def symbols_selection(dict_assets):
    """

    :param dict_assets:
    :return:
    """
    dict_symbols = {
        'long': ['SHFE.rb1905'],
        'short': ['CZCE.MA1905']
    }
    return dict_symbols
