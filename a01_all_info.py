import sqlite3
import pandas as pd
import urllib.request
import sys
import xlrd
import datetime
import time
import csv
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import re
from time import sleep

# 独自モジュールインポート
import common
sys.path.append(common.LIB_DIR)
import s01_gmo

DB_INFO = common.save_path('I01_all.sqlite')

# passconfig
import configparser
config = configparser.ConfigParser()
config.read([common.PASS_FILE])
USER_ID = config.get('gmo', 'USER_ID')
PASSWORD = config.get('gmo', 'PASSWORD')
PASS = config.get('gmo', 'PASS')


class a01_all_info(object):
    def __init__(self):
        self.checked = "TEST"
        self.row_arry = []
        self.empty_dict = {}
        self.send_msg = ""
        self.flag_dir = common.TDNET_FLAG

    def download_file(self, url, filename):
        print('Downloading ... {0} as {1}'.format(url, filename))
        urllib.request.urlretrieve(url, filename)

    def JPbond(self):
        table_name = "JPbond"
        rashio = {}
        UURL = "http://port.jpx.co.jp/jpx/template/quote.cgi?F=tmp/future_daytime"
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)
        # 新規追加確認
        for idx, row in dfs[0].iterrows():
            dict_w = {}
            if row[0].count("長期国債先物"):
                dfs[0] = dfs[0].rename(columns={'Unnamed: 0': '銘柄名','日中取引': '始値', '清算値段': '高値', '制限値幅上限下限': '安値', '建玉残高': '現在値','Unnamed: 7': '前日比', 'Unnamed: 8': '取引高', 'Unnamed: 9': '売り気配', 'Unnamed: 10': '売り気配数量', 'Unnamed: 11': '買い気配','Unnamed: 12': '買い気配数量', 'Unnamed: 13': '清算値段', 'Unnamed: 14': '制限値幅上限下限', 'Unnamed: 15': '建玉残高'})
                for ii in range(len(row)):
                    if str(row[ii]).count("("):
                        sp = str(row[ii]).split("(")
                        dict_w[dfs[0].columns[ii]] = sp[0]
                    else:
                        dict_w[dfs[0].columns[ii]] = str(row[ii])
                break
        common.insertDB3(DB_INFO, table_name, dict_w)

    def bloomberg(self):
        AA = ["energy", "metals", "agriculture"]
        BB = ["energy", "markets/commodities/futures/metals","markets/commodities/futures/agriculture"]
        for num in range(len(AA)):
            table_name = 'bloomberg_list'
            UURL = r"https://www.bloomberg.co.jp/" + BB[num]
            dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)

            # 新規追加確認 https://www.bloomberg.co.jp/markets/commodities/futures/metals
            for i in range(len(dfs)):
                for idx, row in dfs[i].iterrows():
                    dict_w = {}
                    for ii in range(len(row)):
                        dict_w[dfs[i].columns[ii]] = str(row[ii])
                    if "単位" in dict_w.keys():
                        pass
                    else:
                        dict_w["単位"] = ""
                        dict_w["価格"] = ""
                        dict_w["先物契約中心限月"] = ""

                    common.insertDB3(DB_INFO, table_name, dict_w)
        table_name = "bonds"
        UURL = "https://www.bloomberg.co.jp/markets/rates-bonds/government-bonds/us"
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)

        # 新規追加確認
        for i in [0, 1]:
            for idx, row in dfs[i].iterrows():
                dict_w = {}
                for ii in range(len(row)):
                    dict_w[dfs[i].columns[ii]] = str(row[ii])

                common.insertDB3(DB_INFO, table_name, dict_w)

    def bloomberg_rashio(self):
        table_name = "rashio"
        rashio = {}
#        for tick in ["BDIY","USGG5YR","USGG10YR","VIX","DJI", "FVX","SPC","IXIC","TNX"]:

        # "INDU"ダウ,"ES1"SP500,"CCMP"ナスダック
        #https://www.bloomberg.com/quote/CCMP:IND
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) ' 'AppleWebKit/537.36 (KHTML, like Gecko) ' 'Chrome/55.0.2883.95 Safari/537.36 '
        s = requests.session()
        s.headers.update({'User-Agent': ua})
        for tick in [ "CCMP","BDIY", "USGG5YR", "USGG10YR","VIX", "INDU", "ES1"]:
            UURL = "https://www.bloomberg.com/quote/" + tick + ":IND"
            ret = s.get(UURL)
            soup = BeautifulSoup(ret.content, "lxml")
            stocktable = soup.find('div', {'class': 'price'})
            try:
                rashio[tick + "_IND"] = stocktable.text.replace(",", "").replace(".00", "")
            except:
                print(tick)
                self.send_msg += tick + common.create_error(sys.exc_info()) + "\n"
        # 最終行ROWID取得
        rid = common.last_rowid(DB_INFO, table_name)
        # DBアップデート
        sqls = common.create_update_sql(DB_INFO, rashio, table_name, rid) #最後の引数を削除すると自動的に最後の行

    def N225_N(self):
        table_name = "rashio"
        rashio = info.TOPIX_get('05:30')
        dict_w = s01_gmo.check_new_data()
        rashio['N225openN'] = dict_w['N225openN']
        rashio['N225highN'] = dict_w['N225highN']
        rashio['N225lowN'] = dict_w['N225lowN']
        rashio['N225closeN'] = dict_w['N225closeN']
        # 最終行ROWID取得
        rid = common.last_rowid(DB_INFO, table_name)
        # DBアップデート
        sqls = common.create_update_sql(DB_INFO, rashio, table_name, rid) #最後の引数を削除すると自動的に最後の行

    def traders_web_W(self):
        # 1111111投資動向週間
        table_name = 'investment_weekly'
        UURL = "https://www.traders.co.jp/domestic_stocks/stocks_data/investment_3/investment_3.asp"
        dfs = common.read_html2(common.Chorme_get(UURL), 0)  # header=0,skiprows=0(省略可能)
        temp = common.temp_path("csv", os.path.basename(__file__) + "investment.csv")
        dfs[1].to_csv(temp)
        f = open(temp, 'r')
        dataReader = csv.reader(f)
        # 新規追加確認
        for row in dataReader:
            if row[1] == '最新週':
                dict_w = {'週間': common.env_time()[1][:10], '海外投資家': row[2], '生損保': row[3], '銀行': row[4], '信託銀行': row[5], 'その他金融': row[6], '小計_金融法人': row[7],'事業法人': row[8], 'その他法人': row[9], '投信': row[10], '計_法人': row[11], '現金': row[12], '信用': row[13], '計_現金信用': row[14]}
                # 重複チェック
                sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {
                    'table': table_name}
                sql_pd = common.select_sql(DB_INFO, sqls)
                if len(sql_pd) > 0:
                    if dict_w['海外投資家'] != sql_pd.loc[0, '海外投資家']:
                        common.insertDB3(DB_INFO, table_name, dict_w)
                else:
                    common.insertDB3(DB_INFO, table_name, dict_w)
        print(table_name, dict_w)

    def traders_web_D(self):
        # 33333本日の先物取引情報
        table_name = "futures_op"
        UURL = "https://www.traders.co.jp/domestic_stocks/invest_tool/futures/futures_op.asp"
        # テーブル情報取得
        dfs = pd.read_html(common.Chorme_get(UURL), header=1)
        for ii in range(len(dfs)):
            # テーブル番号検索
            if dfs[ii].columns[0] == "証券会社名":  # 証券会社名
                num = ii
                break
        # Webから取得した情報のカラム名をリスト化
        col_list = [i for i in dfs[num].columns]
        # DB追加のカラム作成
        col_tmp = []
        H = ''
        for i in dfs[num].columns:
            if i.count("Unnamed"):
                if 'Unnamed: 2' == i:
                    col_tmp.append('日付')
                    H = 'P'
                else:
                    col_tmp.append('PUT_CALL')
                    H = 'C'
            else:
                col_tmp.append(H + i.replace(".1", ""))
        # カラムのリネームcol_list→col_tmp
#        col = dict(zip(col_list,col_tmp))
        col = {}
        col = {col_list[i]: col_tmp[i] for i in range(len(col_list))}
        dfs[num] = dfs[num].rename(columns=col)

        # DBからカラム情報取得。ない場合は追加する。
        set_new = [i for i in dfs[num].columns]
        res = common.column_check(DB_INFO, table_name, set_new)
        # DBへのインポート
        for idx, row in dfs[num].iterrows():
            dict_w = {}
            for ii in range(len(row)):
                if str(row[ii]) != str(float("nan")):
                    try:
                        dict_w[dfs[num].columns[ii]] = int(row[ii])
                    except:
                        dict_w[dfs[num].columns[ii]] = row[ii]
                else:
                    dict_w[dfs[num].columns[ii]] = 0
            dict_w['日付'] = common.env_time()[0][:8]
            common.insertDB3(DB_INFO, table_name, dict_w)
        # 本日のカラム取得
        sqls = "select * from futures_op where 日付 = %(key1)s" % {'key1': common.env_time()[0][:8]}
        sql_pd = common.select_sql(DB_INFO, sqls)
        set_new = [i for i in sql_pd.columns if i != 'now' and i != '証券会社名' and i != '日付' and i != 'PUT_CALL']
        # 本日のカラムを対象に合計取得
        sqls = "select SUM(" + "),SUM(".join(set_new) + ") from futures_op where 日付 = '%(key1)s'" % {'key1': common.env_time()[0][:8]}
        sql_pd = common.select_sql(DB_INFO, sqls)
        for i, row in sql_pd.iterrows():
            set_val = []
            for ii in range(len(row)):
                if row[ii] is None:
                    set_val.append(0)
                else:
                    set_val.append(row[ii])

        set_val = common.to_int(set_val)
        col = {}
        col = {set_new[i]: set_val[i] for i in range(len(set_new))}
        col['証券会社名'] = '合計'
        col['日付'] = common.env_time()[0][:8]
        col = common.to_int(col)
        common.insertDB3(DB_INFO, table_name, col)
        print(col)

        # 2222222本日の先物取引情報
        table_name = "futures"
        UURL = "https://www.traders.co.jp/domestic_stocks/invest_tool/futures/futures_top.asp"
        dfs = common.read_html2(common.Chorme_get(UURL), 1)  # header=0,skiprows=0(省略可能)
        for ii in range(len(dfs)):
            if dfs[ii].columns[0] == "SELL":
                num = ii
                break
        # カラムの入れ替え
        CC = ['証券会社名', 'SELL_225', 'BUY_225', 'NET_225', '日付',  'SELL_TOPIX','BUY_TOPIX', 'NET_TOPIX', '更新日', 'SELL_225M', 'BUY_225M', 'NET_225M']
        col_name = {}
        col_name = {dfs[num].columns[c]: CC[c] for c in range(len(dfs[num].columns))}
        dfs[num] = dfs[num].rename(columns=col_name)
        # DBへのインポート
        for idx, row in dfs[num].iterrows():
            dict_w = {}
            for ii in range(len(row)):
                dict_w[dfs[num].columns[ii]] = row[ii]
            dict_w['更新日'] = common.env_time()[1]
            dict_w['日付'] = common.env_time()[0][:8]
            common.insertDB3(DB_INFO, table_name, dict_w)


    def rashio19(self):
        rashio = info.TOPIX_get()
        # 225日次情報
        dict_w = s01_gmo.check_new_data()
        rashio['N225openD'] = dict_w['N225openD']
        rashio['N225highD'] = dict_w['N225highD']
        rashio['N225lowD'] = dict_w['N225lowD']
        rashio['N225closeD'] = dict_w['N225closeD']

        # 本日の相場情報
        table_name = "rashio"
        UURL = "https://www.morningstar.co.jp/RankingWeb/IndicesTable.do"
        # テーブル情報取得
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)
        flag = 0
        for idx, row in dfs[0].iterrows():
            if row[0] == "値上がり" or flag == 1:
                rashio[row[0]] = row[1]
                flag = 1

        # 指数一覧取得
        table_name = "rashio"
        UURL = "https://indexes.nikkei.co.jp/nkave/index"

        ret = requests.get(UURL)
        soup = BeautifulSoup(ret.content, "lxml")
        # カラム名取得
        col_tmp = []
        res = soup.find_all("a", attrs={"class": "list-title font-16 divlink"})
        for a in res:
            col_tmp.append(a.string)
            if a.string == '日経総合株価指数':
                break
        # データ取得
        val_tmp = []
        res = soup.find_all("div", attrs={"class": "col-xs-6 col-sm-2"})
        for a in res:
            val_tmp.append(a.string)
        # 辞書作成
        for i in range(len(col_tmp)):
            #        d = dict(zip(val_tmp,col_tmp))
            if val_tmp[i] is None:
                break
            rashio[col_tmp[i]] = val_tmp[i]
        try: #一時的対応エラー2018/7/19
            # 信用残の推移(週次)
            table_name = "rashio"
            UURL = "https://www.traders.co.jp/margin/transition/transition.asp"
            # テーブル情報取得
            dfs = pd.read_html(common.Chorme_get(UURL), header=0)
            num = len(dfs)-1
            # 最新のみ取得
            print(dfs[num])
            list_w = ["申込日", "売り株数", "売り前週比", "売り金額", "売り前週比","買い株数", "買い前週比", "買い金額", "買い前週比", "損益率", "信用倍率"]
            for idx, row in dfs[num].iterrows():
                if idx == 3:
                    cnt = 0
                    print(len(row))
                    print(len(list_w))
                    for ii in range(len(row)):
                        rashio[list_w[ii]] = row[cnt]
                        cnt += 2
                        if list_w[ii] == "信用倍率":
                            break
                    break
        except:
            self.send_msg += "traders.co.jp_信用残の推移(週次)エラー発生" + "\n"
        common.insertDB3(DB_INFO, table_name, rashio)

    def tocom_up(self):
        AA = ['金', 'ゴールドスポット', '白金', 'プラチナスポット', 'プラッツドバイ原油', 'ゴム']
        BB = ['金 標準取引 (1kg)', 'ゴールドスポット', '白金 標準取引 (500g)','プラチナスポット', 'プラッツドバイ原油',  'ゴム']

        # 信用残の推移(週次)
        UURL = "http://www.tocom.or.jp/jp/souba/baibai_top10/index.html"
        # テーブル情報取得
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)
        for ii in range(1, len(dfs)):
            rashio = {}
            for i in range(len(AA)):
                if len(dfs[ii]) > 10:
                    if dfs[ii].columns[0].replace("\n", "").replace(" ", "") == BB[i] or dfs[ii].columns[0].replace("\n", "") == BB[i]:
                        table_name = AA[i]
                        print(dfs[ii].columns[0])
                        for idx, row in dfs[ii].iterrows():
                            if idx < 1:
                                continue
                            if idx % 2 == 0:
                                rashio[row[0].replace(" ", "")] = row[1]
                        # ヘッダー存在チェック
                        new_list = [l for l in rashio]
                        print(new_list)
                        aaa = common.column_check(DB_INFO, table_name, new_list)
                        # DBインサート
                        common.insertDB3(DB_INFO, table_name, rashio)
                        break

        table_name = "ゴム"
        UURL = "http://www.tocom.or.jp/jp/market/reference/kurani_rubber.html"
        # テーブル情報取得
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)
        for ii in range(1, len(dfs)):
            rashio = {}
            if dfs[ii].columns[0] == "指定倉庫":
                for idx, row in dfs[ii].iterrows():
                    if idx == 4:
                        for i in range(len(dfs[ii].columns)):
                            if i > 0:
                                rashio[dfs[ii].columns[i].replace("\n\t\t\t", "").replace(" ", "").replace(".", "_")] = row[i]
                        break
                # 最終行ROWID取得
                rid = common.last_rowid(DB_INFO, table_name)
                # DBアップデート
                sqls = common.create_update_sql(DB_INFO, rashio, table_name, rid) #最後の引数を削除すると自動的に最後の行
                break

        table_name = "tocom"
        UURL = "http://www.tocom.or.jp/jp/souba/torikumi/index.html"
        # テーブル情報取得
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)

        CC = ['カテゴリ', '当業者売', '当業者買', '商品先物取引業者売', '商品先物取引業者買',  'ファンド・投資信託売', 'ファンド・投資信託買', '投資家売', '投資家買','取次者経由売', '取次者経由買', '外国商品先物取引業者経由売', '外国商品先物取引業者経由買', '合計売', '合計買']
        col_name = {}
        col_name = {dfs[0].columns[c]: CC[c] for c in range(len(dfs[0].columns))}
        dfs[0] = dfs[0].rename(columns=col_name)
        # DBへのインポート
        for idx, row in dfs[0].iterrows():
            if idx == 0:
                continue
            dict_w = {}
            for ii in range(len(row)):
                dict_w[dfs[0].columns[ii]] = row[ii]
            dict_w['日付'] = common.env_time()[0][:8]
            common.insertDB3(DB_INFO, table_name, dict_w)

    def fx_daily(self):
        AA = ["01", "02", "04", "08", "13", "06", "14", "03"]
        BB = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY","NZDJPY", "CADJPY", "CHFJPY", "EURUSD"]
        table_name = "FX_daily"
        for i in range(len(AA)):
            UURL = "https://info.ctfx.jp/service/market/csv/" + \
                AA[i] + "_" + BB[i] + "_D.csv"
            dfs = pd.read_csv(UURL, header=0, encoding="cp932")
            dict_w = {}
            for idx, row in dfs.iterrows():
                for ii in range(len(row)):
                    if 1 < ii:
                        dict_w[dfs.columns[ii]] = round(float(row[ii]), 4)
                    else:
                        dict_w[dfs.columns[ii]] = row[ii]

                break
            dict_w['通貨ペア'] = BB[i]
            common.insertDB3(DB_INFO, table_name, dict_w)

    def tocom_gen(self):
        AA = ['金', '白金', 'プラッツドバイ原油', 'ゴム', 'とうもろこし', 'ゴールドスポット', 'プラチナスポット']
        BB = [4, 20, 72, 84, 88, 12, 28]

        # 信用残の推移(週次)
        UURL = "http://www.tocom.or.jp/jp/souba/souba_sx/index.html"
        # テーブル情報取得
        dfs = common.read_html2(UURL, 0)  # header=0,skiprows=0(省略可能)
        print(len(dfs))
        print(dfs[100].ix[0, 0])
        if dfs[100].ix[0, 0] != "日中取引計":
            self.send_msg += "TOCOM弦月チェックテーブル構成が変わりました。確認してください" + "\n"

        for ii in range(len(AA)):
            dict_w = {}
            table_name = "限月"+AA[ii]
            for c in range(2):
                cnt = 0
                if c == 0:  # 日中
                    col_list = list(dfs[BB[ii]].columns)
                    num = BB[ii]
                else:  # 夜間
                    col_list = [t + "L" for t in col_list]
                    num -= 2
                df = dfs[num].sort_index(ascending=False)  # ソート
                for idx, row in df.iterrows():
                    for i in range(len(row)):
                        if col_list[i] == ' - ':
                            continue  # スポットは現月がないのでスキップ

                        if cnt == 0:
                            dict_w[col_list[i]] = row[i]
                        else:
                            dict_w[col_list[i]+str(cnt)] = row[i]
                    cnt += 1
            print(DB_INFO, table_name, dict_w)
            common.insertDB3(DB_INFO, table_name, dict_w)

    def TOPIX_get(self, Stime='15:15'):
        table_name = 'topixL'
        yest_day = str(datetime.date.today() - datetime.timedelta(days=0)).replace("-", "/") + ' ' + Stime
        dict_e = {}

        # 限月取得
        dict = {'table': table_name, 'key1': yest_day, 'key2': ''}
        sqls = "select *,rowid from %(table)s where now > '%(key1)s'" % dict
        sql_pd = common.select_sql('I08_futures.sqlite', sqls)
        num = len(sql_pd)-2
        gen = sql_pd.loc[num, '限月']
        # 限月の妥当性チェック 使えるか?
        if sql_pd.loc[num, '現在値'] == '--':
            gen = sql_pd.loc[num+1, '限月']
        # 終値期限now取得
        dict = {'table': table_name, 'key2': yest_day, 'key3': gen}
        sqls = "select *,SUBSTR(now,12,2) as T,rowid from %(table)s where 限月 = '%(key3)s' and  now > '%(key2)s'" % dict
        sql_pd = common.select_sql('I08_futures.sqlite', sqls)
        num = len(sql_pd)-1
        dict_e['TOPIXnow' + Stime[:2]] = sql_pd.loc[0, 'now']
        dict_e['TOPIX_S' + Stime[:2]] = sql_pd.loc[0, '始値']
        dict_e['TOPIX_H' + Stime[:2]] = sql_pd.loc[0, '高値']
        dict_e['TOPIX_L' + Stime[:2]] = sql_pd.loc[0, '安値']
        dict_e['TOPIX_C' + Stime[:2]] = sql_pd.loc[0, '現在値']
        dict_e['TOPIX_CL' + Stime[:2]] = sql_pd.loc[0, '前日終値']
        dict_e = common.to_number(dict_e)
        return dict_e

    def n225_topix_avg(self):
        dict_w = {}
        yest_day = str(datetime.date.today() - datetime.timedelta(days=30)).replace("-", "/")
        dict = {'table': 'rashio', 'key1': yest_day}
        sqls = "select *,rowid from %(table)s where now > '%(key1)s'" % dict
        sql_pd = common.select_sql('I01_all.sqlite', sqls)
        num = len(sql_pd)-1
        dict_w['N225_乖離avg30'] = round(sql_pd.loc[num, 'N225closeD'] / sql_pd.N225closeD.rolling(num).mean()[num],3)
        dict_w['N225_HighLow30'] = round((sql_pd.loc[num, 'N225closeD'] - sql_pd['N225closeD'].min()) / (sql_pd['N225closeD'].max() - sql_pd['N225closeD'].min()),3)
        dict_w['TOPIX_乖離avg30'] = round(sql_pd.loc[num, 'TOPIX_C15'] / sql_pd.TOPIX_C15.rolling(num).mean()[num],3)
        dict_w['TOPIX_HighLow30'] = round((sql_pd.loc[num, 'TOPIX_C15'] - sql_pd['TOPIX_C15'].min()) / (sql_pd['TOPIX_C15'].max() - sql_pd['TOPIX_C15'].min()),3)
        #DBの型変換する。
        dict_w = common.to_number(dict_w)

        # 最終行ROWID取得
        rid = common.last_rowid('I01_all.sqlite', 'rashio')
        # DBアップデート
        sqls = common.create_update_sql('I01_all.sqlite', dict_w, 'rashio', rid) #最後の引数を削除すると自動的に最後の行
        return dict_w

    def work4(self):
        # 2222222本日の先物取引情報
        table_name = "futures"
        UURL = "https://www.traders.co.jp/domestic_stocks/invest_tool/futures/futures_top.asp"
        dfs = common.read_html(common.Chorme_get(UURL), 1)  # header=0,skiprows=0(省略可能)
        for ii in range(len(dfs)):
            print(ii,dfs[ii].columns[0])
            if dfs[ii].columns[0] == "SELL":
                num = ii
                break
        # カラムの入れ替え
        CC = ['証券会社名', 'SELL_225', 'BUY_225', 'NET_225', '日付',  'SELL_TOPIX','BUY_TOPIX', 'NET_TOPIX', '更新日', 'SELL_225M', 'BUY_225M', 'NET_225M']
        col_name = {}
        col_name = {dfs[num].columns[c]: CC[c] for c in range(len(dfs[num].columns))}
        dfs[num] = dfs[num].rename(columns=col_name)
        # DBへのインポート
        for idx, row in dfs[num].iterrows():
            dict_w = {}
            for ii in range(len(row)):
                dict_w[dfs[num].columns[ii]] = row[ii]
            dict_w['更新日'] = common.env_time()[1]
            dict_w['日付'] = common.env_time()[0][:8]
            common.insertDB3(DB_INFO, table_name, dict_w)


        # 信用残の推移(週次)
        table_name = "rashio"
        UURL = "https://www.traders.co.jp/margin/transition/transition.asp"
        # テーブル情報取得
        dfs = pd.read_html(common.Chorme_get(UURL), header=0)
        num = len(dfs)-1
        # 最新のみ取得
        print(dfs[num])
        list_w = ["申込日", "売り株数", "売り前週比", "売り金額", "売り前週比","買い株数", "買い前週比", "買い金額", "買い前週比", "損益率", "信用倍率"]
        for idx, row in dfs[num].iterrows():
            if idx == 3:
                cnt = 0
                print(len(row))
                print(len(list_w))
                for ii in range(len(row)):
                    rashio[list_w[ii]] = row[cnt]
                    cnt += 2
                    if list_w[ii] == "信用倍率":
                        break
                break
        common.insertDB3(DB_INFO, table_name, rashio)



    def work3(self):
        allLines = open("test.txt",encoding="utf-8").read()
        print(allLines)
        exit()
#        f = open("TEST.CSV", 'r')
#        dataReader = csv.reader(f)
#        for row in dataReader:
#            print(row)
#            exit()

#        exit()
        # 新規追加確認
#        for row in dataReader:

        # 2222222本日の先物取引情報
        table_name = "futures"
        UURL = "https://www.traders.co.jp/domestic_stocks/invest_tool/futures/futures_top.asp"
#        res = common.Chorme_get(UURL)
        browser = webdriver.PhantomJS()
        # ライブスターログイン画面にアクセス
        browser.get(UURL)

        common.create_file("test.txt", browser.page_source)
        exit(9)
        dfs = pd.read_html(res, header=0)
        for ii in range(len(dfs)):
            print("XXX",ii,dfs[ii].columns[0])
            if dfs[ii].columns[0] == "先物・手口情報":
                num = ii +1
                break
        dfs[num].to_csv("TEST.CSV")

        common.create_file("test.txt",dfs[num])
        # カラムの入れ替え
        CC = ['証券会社名', 'SELL_225', 'BUY_225', 'NET_225', '日付',  'SELL_TOPIX','BUY_TOPIX', 'NET_TOPIX', '更新日', 'SELL_225M', 'BUY_225M', 'NET_225M']
        col_name = {}
        col_name = {dfs[num].columns[c]: CC[c] for c in range(len(dfs[num].columns))}
        dfs[num] = dfs[num].rename(columns=col_name)
        # DBへのインポート
        for idx, row in dfs[num].iterrows():
            dict_w = {}
            for ii in range(len(row)):
                dict_w[dfs[num].columns[ii]] = row[ii]
            dict_w['更新日'] = common.env_time()[1]
            dict_w['日付'] = common.env_time()[0][:8]
            common.insertDB3(DB_INFO, table_name, dict_w)

    def work4(self,UURL):
        # 2222222本日の先物取引情報
        browser = webdriver.PhantomJS()
        browser.get(UURL)
        res = browser.page_source
        common.create_file("margin.txt", res)
        res.to_csv("TEST.CSV")
        dfs = pd.read_html(res, 0)  # header=0,skiprows=0(省略可能)
        for ii in range(len(dfs)):
            print("××××", ii, dfs[ii].columns[0])
#        dfs[num].to_csv("TEST.CSV")

if __name__ == '__main__':
    info = a01_all_info()
#    info.work3()  # 修正必要 週次対応#www.traders.co.jp
    UURL = "https://www.traders.co.jp/domestic_stocks/invest_tool/futures/futures_top.asp"
    UURL = "https://www.traders.co.jp/margin/transition/transition.asp"
    info.work4(UURL)
    print(info.send_msg)
    exit()
    argvs = sys.argv
    if argvs[1] == "up6":  # 650
        info.tocom_gen()

    if argvs[1] == "up7":  # 710
        info.fx_daily()
        info.bloomberg()
        info.N225_N()
        info.bloomberg_rashio()

    if argvs[1] == "up19":
        info.JPbond()  # 修正必要 週次対応
        try:
            info.rashio19()  # 修正必要 週次対応
            info.traders_web_W()  # 修正必要 週次対応
            info.traders_web_D()  # 修正必要 週次対応 未対応
        except:
            info.send_msg += "tradersエラー" + "\n"
        info.tocom_up()
        info.n225_topix_avg()

    if info.send_msg != "":
        common.mail_send(u'スクレイピングALL', info.send_msg)

    print("end", __file__)
