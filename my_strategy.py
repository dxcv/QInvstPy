import numpy as np
import pandas as pd


class MyStrategy:

    def __init__(self, ys, **kwargs):
        self.ys = ys
        self.kwargs = kwargs

    def write_py(self, strategy_name, str_strategy, file_path='./trading_strategies/'):
        file = open(file_path+strategy_name+'.py', 'w')
        file.write(str_strategy)
        print('保存成功')
        file.close()

