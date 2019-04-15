from datetime import datetime
from contextlib import closing
from tqsdk import TqApi, TqSim
from tqsdk.tools import DataDownloader

api = TqApi(TqSim())
download_tasks = {}
# # 下载从 2018-01-01 到 2019-01-01 的 ru指数 15分钟线数据
# download_tasks["ru_i_15min"] = DataDownloader(api, symbol_list="KQ.i@SHFE.ru", dur_sec=15 * 60,
#                                               start_dt=date(2018, 1, 1), end_dt=date(2019, 1, 1),
#                                               csv_file_name="ru_i_15min.csv")
# # 下载从 2018-01-01 到 2019-01-01 的 ni指数 30分钟线数据
# download_tasks["ni_i_30min"] = DataDownloader(api, symbol_list="KQ.i@SHFE.ni", dur_sec=30 * 60,
#                                               start_dt=date(2018, 1, 1), end_dt=date(2019, 1, 1),
#                                               csv_file_name="ni_i_30min.csv")
# # 下载从 2018-01-01 到 2019-01-01 的 ma指数 1小时线数据
# download_tasks["ma_i_1h"] = DataDownloader(api, symbol_list="KQ.i@CZCE.MA", dur_sec=60 * 60,
#                                               start_dt=date(2018, 1, 1), end_dt=date(2019, 1, 1),
#                                               csv_file_name="ma_i_1h.csv")
# # 下载从 2018-01-01 到 2019-01-01 的 rb指数 2小时线数据
# download_tasks["rb_i_2h"] = DataDownloader(api, symbol_list="KQ.i@SHFE.rb", dur_sec=60 * 60 * 2,
#                                               start_dt=date(2018, 1, 1), end_dt=date(2019, 1, 1),
#                                               csv_file_name="rb_i_2h.csv")
# 下载从 2019-01-01 到 2019-02-24 的 IF1903 1min数据
download_tasks["IF1904_1min"] = DataDownloader(api, symbol_list="CFFEX.IF1904", dur_sec=60,
                                               start_dt=datetime(2019, 3, 13), end_dt=datetime(2019, 4, 14),
                                               csv_file_name="IF1904_1min.csv")
# 使用with closing机制确保下载完成后释放对应的资源
with closing(api):
    while not all([v.is_finished() for v in download_tasks.values()]):
        api.wait_update()
        print("progress: ", {k: ("%.2f%%" % v.get_progress()) for k, v in download_tasks.items()})
