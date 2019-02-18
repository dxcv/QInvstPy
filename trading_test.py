import os
import datetime as dt

import numpy as np
import pandas as pd

from tqsdk import TqApi, TqSim, TqAccount
from contextlib import closing

# 创建API实例，需要指定交易帐号，or"SIM"
# api = TqApi(TqAccount('G光大期货', '30500071', 'Gd123456'))
api = TqApi("SIM", "ws://10.88.27.135:7777")

# quote = api.get_quote("SHFE.rb1905")
# # "datetime": "",  # "2017-07-26 23:04:21.000001" (行情从交易所发出的时间(北京时间))
# # "ask_price1": float("nan"),  # 6122.0 (卖一价)
# # "ask_volume1": 0,  # 3 (卖一量)
# # "bid_price1": float("nan"),  # 6121.0 (买一价)
# # "bid_volume1": 0,  # 7 (买一量)
# # "last_price": float("nan"),  # 6122.0 (最新价)
# # "highest": float("nan"),  # 6129.0 (当日最高价)
# # "lowest": float("nan"),  # 6101.0 (当日最低价)
# # "open": float("nan"),  # 6102.0 (开盘价)
# # "close": float("nan"),  # nan (收盘价)
# # "average": float("nan"),  # 6119.0 (当日均价)
# # "volume": 0,  # 89252 (成交量)
# # "amount": float("nan"),  # 5461329880.0 (成交额)
# # "open_interest": 0,  # 616424 (持仓量)
# # "settlement": float("nan"),  # nan (结算价)
# # "upper_limit": float("nan"),  # 6388.0 (涨停价)
# # "lower_limit": float("nan"),  # 5896.0 (跌停价)
# # "pre_open_interest": 0,  # 616620 (昨持仓量)
# # "pre_settlement": float("nan"),  # 6142.0 (昨结算价)
# # "pre_close": float("nan"),  # 6106.0 (昨收盘价)
# # "price_tick": float("nan"),  # 10.0 (合约价格单位)
# # "price_decs": 0,  # 0 (合约价格小数位数)
# # "volume_multiple": 0,  # 10 (合约乘数)
# # "max_limit_order_volume": 0,  # 500 (最大限价单手数)
# # "max_market_order_volume": 0,  # 0 (最大市价单手数)
# # "min_limit_order_volume": 0,  # 1 (最小限价单手数)
# # "min_market_order_volume": 0,  # 0 (最小市价单手数)
# # "underlying_symbol": "",  # SHFE.rb1901 (标的合约)
# # "strike_price": float("nan"),  # nan (行权价)
# # "change": float("nan"),  # −20.0 (涨跌)
# # "change_percent": float("nan"),  # −0.00325 (涨跌幅)
# # "expired": False,  # False (合约是否已下市)
#
# while True:
#     api.wait_update()
#     print(quote['last_price'])

data_length = 300
kline = api.get_kline_serial("SHFE.rb1905", duration_seconds=1*60,
                             data_length=min(8964, data_length))
# "datetime": 0,  # 1501080715000000000 (K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
# "open": float("nan"),  # 51450.0 (K线起始时刻的最新价)
# "high": float("nan"),  # 51450.0 (K线时间范围内的最高价)
# "low": float("nan"),  # 51450.0 (K线时间范围内的最低价)
# "close": float("nan"),  # 51450.0 (K线结束时刻的最新价)
# "volume": 0,  # 11 (K线时间范围内的成交量)
# "open_oi": 0,  # 27354 (K线起始时刻的持仓量)
# "close_oi": 0,  # 27355 (K线结束时刻的持仓量)

while True:
    api.wait_update()
    # 判断最后一根K线的时间是否有变化，如果发生变化则表示新产生了一根K线
    if api.is_changing(kline[-1], "datetime"):
        # datetime: 自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        print("新K线", dt.datetime.fromtimestamp(kline[-1]["datetime"]/1e9))
        ys = pd.Series(data=kline.close[-300:],
                       index=[str(dt.datetime.fromtimestamp(i/1e9)) for i in kline.datetime[-300:]]
                       )
        print(ys)
        print(type(ys))

# data_length = 200
# serial = api.get_tick_serial("SHFE.cu1903",
#                              data_length=min(8964, data_length))
# # "datetime": 0,  # 1501074872000000000 (tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
# # "last_price": float("nan"),  # 3887.0 (最新价)
# # "average": float("nan"),  # 3820.0 (当日均价)
# # "highest": float("nan"),  # 3897.0 (当日最高价)
# # "lowest": float("nan"),  # 3806.0 (当日最低价)
# # "ask_price1": float("nan"),  # 3886.0 (卖一价)
# # "ask_volume1": 0,  # 3 (卖一量)
# # "bid_price1": float("nan"),  # 3881.0 (买一价)
# # "bid_volume1": 0,  # 18 (买一量)
# # "volume": 0,  # 7823 (当日成交量)
# # "amount": float("nan"),  # 19237841.0 (成交额)
# # "open_interest": 0,  # 1941 (持仓量)
#
# while True:
#     api.wait_update()
#     print(serial[-1]["bid_price1"], serial[-1]["ask_price1"])
#
#
#
# account = api.get_account()
# # dict
# # "currency": "",  # "CNY" (币种)
# # "pre_balance": float("nan"),  # 9912934.78 (昨日账户权益)
# # "static_balance": float("nan"),  # (静态权益)
# # "balance": float("nan"),  # 9963216.55 (账户权益)
# # "available": float("nan"),  # 9480176.15 (可用资金)
# # "float_profit": float("nan"),  # 8910.0 (浮动盈亏)
# # "position_profit": float("nan"),  # 1120.0(持仓盈亏)
# # "close_profit": float("nan"),  # -11120.0 (本交易日内平仓盈亏)
# # "frozen_margin": float("nan"),  # 0.0(冻结保证金)
# # "margin": float("nan"),  # 11232.23 (保证金占用)
# # "frozen_commission": float("nan"),  # 0.0 (冻结手续费)
# # "commission": float("nan"),  # 123.0 (本交易日内交纳的手续费)
# # "frozen_premium": float("nan"),  # 0.0 (冻结权利金)
# # "premium": float("nan"),  # 0.0 (本交易日内交纳的权利金)
# # "deposit": float("nan"),  # 1234.0 (本交易日内的入金金额)
# # "withdraw": float("nan"),  # 890.0 (本交易日内的出金金额)
# # "risk_ratio": float("nan"),  # 0.048482375 (风险度)
#
# with closing(api):
#     while True:
#         api.wait_update()
#         if api.is_changing(account):
#             print('available:', account['available'])
#             print('protf:', account['float_profit'])

