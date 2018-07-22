#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
from selenium import webdriver
import csv, os ,sys
import urllib.request
import lxml.html
import datetime
import re
import inspect
from bs4 import BeautifulSoup
import json
import requests
import sqlite3
import pandas as pd
import pybitflyer

#独自モジュールインポート
import common
sys.path.append(common.LIB_DIR)
import f01_sbi
import f02_gmo

FX_DB = common.save_path('I07_fx.sqlite')
FX_DB_BYBY = common.save_path('B03_fx_stg.sqlite')

#passconfig
import configparser
config = configparser.ConfigParser()
config.read([common.PASS_FILE])
USER_ID=config.get('gmo','USER_ID')
PASSWORD=config.get('gmo','PASSWORD')
PASS=config.get('gmo','PASS')

class kabucom:
    def __init__(self,num):
        self.empty_dict = {}
        self.save_dir = "07_fx"
        t = datetime.datetime.now()
        self.date = t.strftime("%Y%m%d%H%M")
        self.timef = t.strftime("%Y/%m/%d %H:%M:%S")
        self.send_msg = ""

    def info_get(self):
        # 定数設定
        SITE_URL='https://sec-sso.click-sec.com/mf/'


        browser = webdriver.PhantomJS()
        browser.get(SITE_URL)

        # ログイン処理
        uid = browser.find_element_by_name('j_username')
        password = browser.find_element_by_name('j_password')
        uid.send_keys(USER_ID)
        password.send_keys(PASSWORD)
        browser.find_element_by_name('LoginForm').click()
        browser.find_element_by_link_text('ﾚｰﾄ一覧(新規注文)').click()
        for m in re.finditer(r'">(.+?)</a>[(&nbsp;)]*(.+?)-', browser.page_source, re.UNICODE):
            self.empty_dict[m.groups()[0]] = m.groups()[1].replace(",","")
        common.insertDB3(FX_DB,"gmofx",self.empty_dict)

    def info_gaitame(self):
        url = "http://www.gaitameonline.com/rateaj/getrate"
        req = requests.get(url)
        data = json.loads(req.text)
        for i in range(len(data["quotes"])):
            dict_list = {"currencyPairCode":"","open":"0","high":"0","low":"0","bid":"0","ask":"0"}
            tablename = "gaitame_" + data["quotes"][i]["currencyPairCode"]
            common.insertDB3(FX_DB,tablename,data["quotes"][i])


    #移動平均を基準とした上限・下限のブレイクアウト
    def breakout_ma_std(self, window, multi, para_key1, para_key2, col, byby, type):
        data = {'Close':'','ma_m':'','ma_s':'','ub':'','lb':'','pl':'','n':'','Long':'', 'Short':'','L_PL':'', 'S_PL':'','L_SUM':'','S_SUM':''}
        print("code",col)
        #GMOFX情報取得
        stuts = 0
        sqls = "select now,\"" + col + "\" from gmofx where rowid=(select max(rowid) from gmofx);"
        sql_pd = common.select_sql(FX_DB,sqls)
        data['Close'] = sql_pd.loc[0,col]


        #データ更新、データフレームに引き出す
        tablename = col.replace(r"/","") + "_" + byby
        common.insertDB3(FX_DB_BYBY,tablename,data)
        col_name = ', '.join([k for k in data.keys()])
        sqls = "select now," + col_name + " from " + tablename
        tsd = common.select_sql(FX_DB_BYBY,sqls)

        #仕掛け処理更新
        if len(tsd) > window:
            tsd['ma_m']=tsd.Close.rolling(window).mean().dropna()
            tsd['ma_s']=tsd.Close.rolling(window).std()
            tsd['ub']=tsd.ma_m+tsd.ma_s*multi
            tsd['lb']=tsd.ma_m-tsd.ma_s*multi
            tsd['pl']=tsd['pl'].shift(1)
            tsd['n']=tsd['n'].shift(1)
            tsd['L_SUM']=tsd['L_SUM'].shift(1)
            tsd['S_SUM']=tsd['S_SUM'].shift(1)
            lrow = len(tsd) - 1
            ind = datetime.datetime.now()
            c = round(float(tsd.Close[lrow]),4)
            ma_m = round(float(tsd.ma_m[lrow]),4)
            ma_s = round(float(tsd.ma_s[lrow]),4)
            ub = round(float(tsd.ub[lrow]),4)
            lb = round(float(tsd.lb[lrow]),4)
            L_PL = ""
            S_PL = ""
            pl = int(tsd.pl[lrow])
            n = tsd.n[lrow]
            L_SUM = round(float(tsd.L_SUM[lrow]), 4)

            #一時的後でelseは削除
            try:
                S_SUM = round(float(tsd.S_SUM[lrow]), 4)
            except:
                S_SUM = 0

            if n != "":
                n = round(float(tsd.n[lrow]),4)

            if c<lb and pl==0 and ind.hour >= para_key1 and ind.hour <= para_key2 :#entry short-position
                stuts = -1 * type
                n=c
                pl=-1
                #売り仕掛け

            if c>ma_m and pl<0:#exit short-position
                stuts = -2 * type
                S_PL=round(float(n-c),4)
                n=""
                pl=0
                S_SUM+=S_PL
                #売り仕切り


            if c>ub and pl==0 and ind.hour >= para_key1 and ind.hour <= para_key2:#entry short-position
                stuts = 1 * type
                n=c
                pl=1
                #買い仕掛け

            if c<ma_m and  pl>0:#exit short-position
                stuts = 2 * type
                L_PL=round(float(c-n),4)
                n=""
                pl=0
                L_SUM+=L_PL
                #買い仕切り

            dict = {'table':tablename,'key1':ind,'key2':ma_m,'key3':ma_s,'key4':ub,'key5':lb,'key6':pl,'key7':n,'key8':L_PL,'key9':S_PL,'key10':L_SUM,'key11':S_SUM}
            sqls = "UPDATE %(table)s SET ma_m = '%(key2)s', ma_s = '%(key3)s',ub = '%(key4)s', lb = '%(key5)s' ,pl = '%(key6)s', n = '%(key7)s', L_PL = '%(key8)s' ,S_PL = '%(key9)s', L_SUM = '%(key10)s', S_SUM = '%(key11)s' where rowid=(select max(rowid) from %(table)s)" % dict
            common.db_update(FX_DB_BYBY,sqls)
            return stuts


    #過去の高値・安値を用いたブレイクアウト戦略
    def breakout_simple(self, window0, window9, para_key1, para_key2, col, byby, type):
        data = {'Close':'','ub0':'','lb0':'','ub9':'','lb9':'','pl':'','n':'','Long':'', 'Short':'','L_PL':'', 'S_PL':'','L_SUM':'','S_SUM':''}
        #GMOFX情報取得
        stuts = 0
        sqls = "select now,\"" + col + "\" from gmofx where rowid=(select max(rowid) from gmofx) ;"
        sql_pd = common.select_sql(FX_DB,sqls)
        data['Close'] = sql_pd.loc[0,col]
        #データ更新、データフレームに引き出す
        tablename = col.replace(r"/", "") + "_" + byby
        common.insertDB3(FX_DB_BYBY,tablename,data)
        col_name = ', '.join([k for k in data.keys()])
        sqls = "select now," + col_name + " from " + tablename
        tsd = common.select_sql(FX_DB_BYBY, sqls)

        #仕掛け処理更新
        if len(tsd) > window9:
            y=tsd
            y['ub0']=y['Close'].rolling(window0).max()
            y['lb0']=y['Close'].rolling(window0).min()
            y['ub9']=y['Close'].rolling(window9).max()
            y['lb9']=y['Close'].rolling(window9).min()
            y['pl']=y['pl'].shift(1)
            y['n']=y['n'].shift(1)
            y['S_SUM']=y['S_SUM'].shift(1)
            y['L_SUM'] = y['L_SUM'].shift(1)
            lrow = len(y) - 1
            lrow2 = len(y) - 2
            try:
                c = round(float(y.Close[lrow]), 4)
            except:
                print(y.Close[lrow])
                exit()
            ind = datetime.datetime.now()
            ub0 = round(float(y.ub0[lrow]),4)
            lb0 = round(float(y.lb0[lrow]),4)
            ub9 = round(float(y.ub9[lrow]),4)
            lb9 = round(float(y.lb9[lrow]),4)
            #追加
            ub0l = round(float(y.ub0[lrow2]),4)
            lb0l = round(float(y.lb0[lrow2]),4)
            ub9l = round(float(y.ub9[lrow2]),4)
            lb9l = round(float(y.lb9[lrow2]),4)

            L_PL = ""
            S_PL = ""
            pl = int(y.pl[lrow])
            n = y.n[lrow]
            L_SUM = round(float(y.L_SUM[lrow]),4)
            #一時的後でelseは削除
            try:
                S_SUM = round(float(tsd.S_SUM[lrow]), 4)
            except:
                S_SUM = 0

            if n != "":
                n = round(float(y.n[lrow]), 4)

            if c<lb0l and pl==0 and para_key1 <= ind.hour <= para_key2:#entry short-position
                stuts = -1 * type
                #売り仕掛け(typeを使って買い売り逆転)
                n=c
                pl=-1

            if c>ub9l and pl<0:#exit short-position
                stuts = -2 * type
                #売り仕切り
                S_PL=n-c
                n=""
                pl=0

            if c>ub0l and pl==0 and para_key1 <= ind.hour <= para_key2:#entry short-position
                stuts = 1 * type
                #買い仕掛け
                n=c
                pl=1

            if c<lb9l and pl>0:#exit short-position
                stuts = 2 * type
                #買い仕切り
                L_PL=c-n
                n=""
                pl=0

            dict = {'table':tablename,'key1':ind,'key2':ub0,'key3':lb0,'key4':ub9,'key5':lb9,'key6':pl,'key7':n,'key8':L_PL,'key9':S_PL,'key10':L_SUM,'key11':S_SUM}
            sqls = "UPDATE %(table)s SET ub0 = '%(key2)s', lb0 = '%(key3)s',ub9 = '%(key4)s', lb9 = '%(key5)s' ,pl = '%(key6)s', n = '%(key7)s', \
            L_PL = '%(key8)s' ,S_PL = '%(key9)s', L_SUM = '%(key10)s', S_SUM = '%(key11)s' where rowid=(select max(rowid) from %(table)s)" % dict
            common.db_update(FX_DB_BYBY,sqls)
            return stuts

    def fx_byby_exec(self,PL,code,amount,title):

        if PL == 0:
            return 0

        if PL == 1:
            bybypara = {'code': code, 'amount': amount, 'buysell': '買', 'kubun': '新規', 'nari_hiki': '0', 'settle': '', 'comment': title, 'now': '0'}
#            exec_time = f01_sbi.sbi_fx_main(bybypara)
            self.send_msg += title + "_" + code + ":新規買い" + "\n"
            exec_time = f02_gmo.gmo_fx_main(bybypara)

        if PL == 2:
            bybypara = {'code': code, 'amount': amount, 'buysell': '買', 'kubun': '決済', 'nari_hiki': '0', 'settle': '', 'comment': title, 'now': '0'}
#            exec_time = f01_sbi.sbi_fx_main(bybypara)
            self.send_msg += title + "_" + code + ":決算買い" + "\n"
            exec_time = f02_gmo.gmo_fx_main(bybypara)

        if PL == -1:
            bybypara = {'code': code, 'amount': amount, 'buysell': '売', 'kubun': '新規', 'nari_hiki': '0', 'settle': '', 'comment': title, 'now': '0'}
#            exec_time = f01_sbi.sbi_fx_main(bybypara)
            self.send_msg += title + "_" + code + ":新規売り" + "\n"
            exec_time = f02_gmo.gmo_fx_main(bybypara)

        if PL == -2:
            bybypara = {'code': code, 'amount': amount, 'buysell': '売', 'kubun': '決済', 'nari_hiki': '0', 'settle': '', 'comment': title, 'now': '0'}
#            exec_time = f01_sbi.sbi_fx_main(bybypara)
            self.send_msg += title + "_" + code + ":決算売り" + "\n"
            exec_time = f02_gmo.gmo_fx_main(bybypara)

        if os.uname()[1] == 'sub0000545757' and bybypara['code'] in ['USD/JPY','EUR/USD']:
            import f01_sbi_fire
            bybypara['amount'] = 100
            exec_time = f01_sbi_fire.sbi_fx_main(bybypara)
        return exec_time

    def fx_update(self):
        #BacktestReport
        byby = 'BacktestReport'
        window=350
        window=100
        multi=2.5

        fx = u'AUD/JPY'
        s_time = 17
        e_time = 20
        PL = self.breakout_ma_std(window,multi,s_time,e_time,fx,byby,1)
#        times = self.fx_byby_exec(PL,fx,2,byby)

        fx = u'GBP/JPY'
        s_time = 2
        e_time = 15
        PL = self.breakout_ma_std(window,multi,s_time,e_time,fx,byby,1)
        times = self.fx_byby_exec(PL,fx,2,byby)

        #breakout_simple
        byby = "breakout_simple"
        window0=20
        window9=10

        fx = u'AUD/JPY'
        s_time = 3
        e_time = 6
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
        times = self.fx_byby_exec(PL,fx,3,byby)

        fx = u'USD/JPY'
        s_time = 4
        e_time = 6
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
        if os.uname()[1] == 'sub0000545757':
            times = self.fx_byby_exec(PL,fx,1,byby)

        fx = u'GBP/JPY'
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
        times = self.fx_byby_exec(PL,fx,3,byby)

        fx = u'AUD/USD'
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
        times = self.fx_byby_exec(PL,fx,3,byby)

        fx = u'GBP/USD'
        s_time = 4
        e_time = 7
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
#        times = self.fx_byby_exec(PL,fx,3,byby)

        fx = u'EUR/USD'
        s_time = 5
        e_time = 6
        PL=self.breakout_simple(window0,window9,s_time,e_time,fx,byby,-1)
        if os.uname()[1] == 'sub0000545757':
            times = self.fx_byby_exec(PL,fx,1,byby)

    def click365_info(self):
        table_name = "click365"
        UURL = "http://tfx.jfx.jiji.com/cfd/quote"
        dfs = pd.read_html(UURL, header=0)
        # 新規追加確認
        dict_w = {}
        for idx, row in dfs[0].iterrows():
            for ii in range(1,len(row)):
                dict_w[row['商品名'] + "_" + dfs[0].columns[ii]] = row[ii]
        #重複チェック
        dbck = {'table_name': table_name,
                '日経225_買気配(数量)': dict_w['日経225_買気配(数量)'], '日経225_売気配(数量)': dict_w['日経225_売気配(数量)'], '日経225_直近約定値': dict_w['日経225_直近約定値']}
        res = common.row_check(FX_DB, dbck)
        if res != 1:
            # DBへのインポート
            common.insertDB3(FX_DB, table_name, dict_w)

if __name__ == "__main__":
    info = kabucom(0)
    try:
        info.info_get()
    except:
        sleep(60)
        info.info_get()

    info.info_gaitame()
    common.mail_send(u'FX取引情報', info.send_msg)
    info.fx_update()
    info.click365_info()

    print("end",__file__)
