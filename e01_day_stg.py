import pandas as pd
import os
import sys
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import common
sys.path.append(common.LIB_DIR)
import f02_gmo
import f03_ctfx
import datetime

class e01_day_stg(object):
    def __init__(self):
        self.send_msg = ""
        self.INFO_DB = common.save_path('B05_cfd_stg.sqlite')
    # 3つの移動平均を使った戦略

    def breakout_ma_three(self, window0, window9, window5, col,  table):
        status = 0
        data = {'L_flag': "", 'S_flag': "", 'S_PL': "", 'L_PL': "", 'S3_R': ""}
        sqls = 'select "%(key1)s" from %(table)s where rowid=(select max(rowid) from %(table)s) ;' % {'table': table, 'key1': col}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        data['S3_R'] = float(sql_pd.loc[0, col])
        # データ更新、データフレームに引き出す
        tablename = col + "_breakout_ma_three"
        common.insertDB3(self.INFO_DB, tablename, data)
        col_name = ', '.join([k for k in data.keys()])
        sqls = "select *,rowid from %(table)s" % {'table': tablename}
        tsd = common.select_sql(self.INFO_DB, sqls)
        tsd.S3_R.dropna()
        cnt = len(tsd) - 1
        if cnt < 10:
            return status
        data['avg_'+str(window0)] = tsd.S3_R.rolling(window0).mean().shift(1)[cnt]
        data['avg_'+str(window9)] = tsd.S3_R.rolling(window9).mean().shift(1)[cnt]
        data['avg_'+str(window5)] = tsd.S3_R.rolling(window5).mean().shift(1)[cnt]

        # レポート用
        # init----------------------------------
        cnt2 = len(tsd) - 2
        if tsd.loc[cnt2, 'S_flag'] is None or tsd.loc[cnt2, 'S_flag'] == "":
            S_flag = 0
        else:
            S_flag = float(tsd.loc[cnt2, 'S_flag'])

        if tsd.loc[cnt2, 'L_flag'] is None or tsd.loc[cnt2, 'L_flag'] == "":
            L_flag = 0
        else:
            L_flag = float(tsd.loc[cnt2, 'L_flag'])


        data['S_flag'] = tsd.loc[cnt2, 'S_flag']
        data['L_flag'] = tsd.loc[cnt2, 'L_flag']
        common.to_number(data)
        # entry short-position
        if S_flag == 0 and data['avg_'+str(window0)] < data['avg_'+str(window5)] < data['avg_'+str(window9)]:
            data['S_flag'] = data['S3_R']
            status = -1
        elif (data['avg_'+str(window0)] > data['avg_'+str(window5)] or data['avg_'+str(window5)] > data['avg_'+str(window9)]) and S_flag != 0:  # exit short-position
            data['S_PL'] = S_flag-data['S3_R']
            data['S_flag'] = 0
            status = -2
        # entry short-position
        elif L_flag == 0 and data['avg_'+str(window0)] > data['avg_'+str(window5)] > data['avg_'+str(window9)]:
            data['L_flag'] = data['S3_R']
            status = 1
        elif (data['avg_'+str(window0)] < data['avg_'+str(window5)] or data['avg_'+str(window5)] < data['avg_'+str(window9)]) and L_flag != 0:  # exit short-position
            data['L_PL'] = data['S3_R']-L_flag
            data['L_flag'] = 0
        # rowid取得
        sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': tablename}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        sqls = common.create_update_sql(self.INFO_DB, data, tablename, sql_pd['rowid'][0])

    # クロスオーバー移動平均
    def breakout_ma_two(self, window0, window9, col,  table):
        status = 0
        data = {'L_flag': "", 'S_flag': "", 'S_PL': "", 'L_PL': ""}
        sqls = "select %(key1)s from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': table, 'key1': col}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        data['S3_R'] = float(sql_pd.loc[0, col])

        # データ更新、データフレームに引き出す
        tablename = col + "_breakout_ma_two"
        common.insertDB3(self.INFO_DB, tablename, data)
        sqls = "select *,rowid from " + tablename
        tsd = common.select_sql(self.INFO_DB, sqls)
        tsd.S3_R.dropna()
        cnt = len(tsd) - 1
        if cnt < 10:
            return status

        data['avg_'+str(window0)] = tsd.S3_R.rolling(window0).mean().shift(1)[cnt]
        data['avg_'+str(window9)] = tsd.S3_R.rolling(window9).mean().shift(1)[cnt]

        cnt2 = len(tsd) - 2
        if tsd.loc[cnt2, 'S_flag'] is None or tsd.loc[cnt2, 'S_flag'] == "":
            S_flag = 0
        else:
            S_flag = float(tsd.loc[cnt2, 'S_flag'])

        if tsd.loc[cnt2, 'L_flag'] is None or tsd.loc[cnt2, 'L_flag'] == "":
            L_flag = 0
        else:
            L_flag = float(tsd.loc[cnt2, 'L_flag'])

#        window0 = 32 797.98438
#        window9 = 12 798.41667

        data['S_flag'] = tsd.loc[cnt2, 'S_flag']
        data['L_flag'] = tsd.loc[cnt2, 'L_flag']
        common.to_number(data)
        status = 0
        #仕切り
        if data['avg_'+str(window0)] > data['avg_'+str(window9)] and S_flag != 0:  # exit short-position
            data['S_PL'] = S_flag-data['S3_R']  # レポート用
            data['S_flag'] = 0
            status = -2
        elif data['avg_'+str(window0)] < data['avg_'+str(window9)] and L_flag != 0:  # exit short-position
            data['L_PL'] = data['S3_R']-L_flag  # レポート用
            data['L_flag'] = 0
        #仕掛け
        elif data['avg_'+str(window0)] < data['avg_'+str(window9)] and S_flag == 0:  # entry short-position
            data['S_flag'] = data['S3_R']
            status = -1
        elif data['avg_'+str(window0)] > data['avg_'+str(window9)] and L_flag == 0:  # entry short-position
            data['L_flag'] = data['S3_R']
            status = 1

#            status =  2
        # rowid取得
        sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': tablename}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        sqls = common.create_update_sql(self.INFO_DB, data, tablename, sql_pd['rowid'][0])
        return status

    # フィルター付き高値・安値のブレイクアウト
#        window0 = 2 window9 = 2 f0 = 12 f9 = 2
    def breakout_simple_f(self,  window0, window9, f0, f9, col,  table):
        status = 0
        data = {'L_flag': "", 'S_flag': "", 'L_SUM': "",'S_PL': "", 'L_PL': ""}
        sqls = "select %(key1)s from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': table, 'key1': col}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        data['S3_R'] = float(sql_pd.loc[0, col])

        # データ更新、データフレームに引き出す
        tablename = col + "_breakout_simple_f"
        common.insertDB3(self.INFO_DB, tablename, data)
        sqls = "select *,rowid from " + tablename
        tsd = common.select_sql(self.INFO_DB, sqls)
        tsd.S3_R.dropna()
        cnt = len(tsd) - 1
        if cnt < 10:
            return 0
        data['max_s' + str(window0)] = tsd.S3_R.rolling(window0).max().shift(1)[cnt] #ub0
        data['min_s' + str(window0)] = tsd.S3_R.rolling(window0).min().shift(1)[cnt] #2
        data['max_e' + str(window9)] = tsd.S3_R.rolling(window9).max().shift(1)[cnt] #ub9
        data['min_e' + str(window9)] = tsd.S3_R.rolling(window9).min().shift(1)[cnt] #lb9
        data['avg_l' + str(f0)] = tsd.S3_R.rolling(f0).mean().shift(1)[cnt] #f0
        data['avg_s' + str(f9)] = tsd.S3_R.rolling(f9).mean().shift(1)[cnt] #f9
        # init----------------------------------
        cnt2 = len(tsd) - 2
        if tsd.loc[cnt2, 'S_flag'] is None or tsd.loc[cnt2, 'S_flag'] == "":
            S_flag = 0
        else:
            S_flag = float(tsd.loc[cnt2, 'S_flag'])

        if tsd.loc[cnt2, 'L_flag'] is None or tsd.loc[cnt2, 'L_flag'] == "":
            L_flag = 0
        else:
            L_flag = float(tsd.loc[cnt2, 'L_flag'])

        data['S_flag'] = tsd.loc[cnt2, 'S_flag']
        data['L_flag'] = tsd.loc[cnt2, 'L_flag']
        common.to_number(data)
        c = data['S3_R']
        status = 0

        if c > data['max_e' + str(window9)] and S_flag != 0:  # exit short-position
            data['S_PL'] = S_flag-c  # レポート用
            data['S_flag'] = 0
            status = -2
        elif c < data['min_e' + str(window9)] and L_flag != 0:  # exit short-position
            data['L_PL'] = c-L_flag  # レポート用
            data['L_flag'] = 0
            status = 2
        elif c < data['min_s' + str(window0)] and S_flag == 0 and L_flag == 0 and data['avg_s' + str(f9)] > data['avg_l' + str(f0)]:
            data['S_flag'] = c
            status = -1
        elif c > data['max_s' + str(window0)] and S_flag == 0 and L_flag == 0 and data['avg_s' + str(f9)] < data['avg_l' + str(f0)]:
            data['L_flag'] = c
            status = 1
        """
        #仕切りチェック
        if status == -1 and L_flag != 0:
            print("仕切り1")
            self.byby_exec_fx(2, col, 1)
        if status == 1 and S_flag != 0:
            print("仕切り2")
            self.byby_exec_fx(-2, col, 1)
        """
        # rowid取得
        sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': tablename}
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        sqls = common.create_update_sql(self.INFO_DB, data, tablename, sql_pd['rowid'][0])

        return status

    def stg_main(self):
        window0 = 32
        window9 = 22
        code = u'金スポット'
        table = '_gmo_info'
        PL = self.breakout_ma_two(window0, window9, code, table)
        self.byby_exec_fx(PL, code, 1)
        #何の為？
#        if PL == -1:
#            self.byby_exec_fx(2, code, 1)

        window0 = 10
        window9 = 3
        f0 = 70
        f9 = 80
        code = u'米NQ100'
        table = '_gmo_info'
        PL = self.breakout_simple_f(window0, window9, f0, f9, code, table)
        self.byby_exec_fx(PL, code, 1)

        window0 = 42
        window9 = 52
        window5 = 2
        code = u'米30'
        table = '_gmo_info'
        PL = self.breakout_ma_three(window0, window9, window5, code, table)
        self.byby_exec_fx(PL, code, 1)

        window0 = 32
        window9 = 62
        window5 = 2
        code = u'米S500'
        table = '_gmo_info'
        PL = self.breakout_ma_three(window0, window9, window5, code, table)
        self.byby_exec_fx(PL, code, 1)

        window0 = 22
        window9 = 2
        window5 = 100 #後で100に修正
        code = 'EURJPY'
        table = '_gmo_info'
        PL = self.breakout_ma_three(window0, window9, window5, code, table)
        self.byby_exec_fx(PL, code, 2)

        window0 = 22
        window9 = 12
        window5 = 100  # 後で100に修正
        code = 'EURUSD'
        table = '_gmo_info'
        PL = self.breakout_ma_three(window0, window9, window5, code, table)
        self.byby_exec_fx(PL, code, 2)

        window0 = 2
        window9 = 12
        f0 = 80
        f9 = 40
        code = 'AUDJPY'
        table = '_gmo_info'
        PL = self.breakout_simple_f(window0, window9, f0, f9, code, table)
        self.byby_exec_fx(PL, code, 2)

    def byby_exec_fx(self, PL, code, amount):
        result = 0
        if PL in(1,2,-1,-2):
            if PL == 1:
                bybypara = {'code': code, 'amount': amount, 'buysell': '買', 'kubun': '新規','nari_hiki': '', 'settle': 0, 'comment': code + '_成行買い'}
            if PL == 2:
                # 買い決済
                bybypara = {'code': code, 'amount': amount, 'buysell': '買', 'kubun': '決済','nari_hiki': '', 'settle': -1, 'comment': code + '_買い決済'}
            if PL == -1:
                bybypara = {'code': code, 'amount': amount, 'buysell': '売', 'kubun': '新規','nari_hiki': '', 'settle': 0, 'comment': code + '_成行売り'}
            if PL == -2:
                # 売り決済
                bybypara = {'code': code, 'amount': amount, 'buysell': '売', 'kubun': '決済','nari_hiki': '', 'settle': -1, 'comment': code + '_売り決済'}
        else:
            return result
        print("bybypara1",bybypara)
        if code.count("JPY") or code.count("USD"):
            result, msg, browser = f03_ctfx.f03_ctfx_main(bybypara)
        else:
            for iii in range(3):
                try:
                    result, msg = f02_gmo.gmo_cfd_exec(bybypara)
                    print(msg)
                    if msg.count('正常終了'):
                        break
                except:
                    pass
            else:
                bybypara['status'] = -5
                msg = '異常終了'
                common.insertDB3(self.INFO_DB, "retry", bybypara)

        self.send_msg += bybypara['comment'] + msg + "\n"
        return result

    def retry_check(self):
        sqls = 'select *,rowid from retry where status < 0 ;'
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        for i, row in sql_pd.iterrows():
            common.to_number(row)
            dict_w = {}
            bybypara = dict(row)
            try:
                result, msg = f02_gmo.gmo_cfd_exec(bybypara)
                if str(msg).count('正常終了'):
                    dict_w['status'] = 0
                else:
                    dict_w['status'] = row['status'] + 1
            except:
                dict_w['status'] = row['status'] + 1
                self.send_msg += u'CFDトレードリトライ異常終了_' + bybypara['code'] + "\n"

            sqls = common.create_update_sql(self.INFO_DB, dict_w, 'retry', bybypara['rowid']) #最後の引数を削除すると自動的に最後の行

    def main_test(self, HH):
        return 0
        code = u'米NQ100'
        if HH == 4:
            PL = 1 #買い
        elif HH == 5:
            PL = 2  #買い決済
        else:
            return 0
        self.byby_exec_fx(PL, code, 1)

    def cfd_poji_check(self):
        ok_msg = ""
        list_code, list_type = f02_gmo.info_pojicheck()
        codes, types, amounts = f03_ctfx.f03_ctfx_main({'kubun': 'ポジションチェック','amount':'2,000'})
        # 全テーブル情報取得
        sqls = "select name from sqlite_master where type='table'"
        sql_pd = common.select_sql(self.INFO_DB, sqls)
        for i, rrow in sql_pd.iterrows():
            table_name = rrow['name']
            sp_work = table_name.split("_")
            code = sp_work[0]
            if len(sp_work) != 4:
                continue
            sqls = "select L_flag,S_flag from %(table)s where (L_flag > 0 or S_flag > 0) and rowid=(select max(rowid) from %(table)s) ;" % {'table': table_name}
            sql_pdd = common.select_sql(self.INFO_DB, sqls)
            if len(sql_pdd) > 0:
                if sql_pdd['L_flag'][0] != "":
                    if float(sql_pdd['L_flag'][0]) > 0:
                        type_w = "買"
                if sql_pdd['S_flag'][0] != "":
                    if float(sql_pdd['S_flag'][0]) > 0:
                        type_w = "売"
                #CDFのポジションチェック
                for ii in range(len(list_code)):
                    if list_code[ii] == code and list_type[ii] == type_w:
                        del list_code[ii]
                        del list_type[ii]
                        ok_msg += u'CFDポジション一致_' + code +  "_" + type_w +"\n"
                        break
                else:
                    #FXのポジションチェック
                    for ii in range(len(codes)):
                        if codes[ii] == code and types[ii] == type_w:
                            del codes[ii]
                            del types[ii]
                            del amounts[ii]
                            ok_msg += u'FXポジション一致_' + code + "_" + type_w + "\n"
                            break
                    else:
                        self.send_msg += u'FXポジションなし_' + code + "_" + type_w + "\n"
                        if code.count("JPY") or code.count("USD"):
                            bybypara = {'code': code, 'amount': 2, 'buysell': type_w, 'kubun': '新規', 'nari_hiki': '', 'settle': 0, 'comment': code + '_成行'}
#                            f03_ctfx.f03_ctfx_main(bybypara)
                        else:
                            bybypara = {'code': code, 'amount': 1, 'buysell': type_w, 'kubun': '新規', 'nari_hiki': '', 'settle': 0, 'comment': code + '_成行'}
#                            f02_gmo.gmo_cfd_exec(bybypara)

        if len(list_code) > 0:
            self.send_msg += u'未決済銘柄あり_' + '_'.join([k for k in list_code]) + "\n" + '_'.join([k for k in list_type]) + "\n"
            for ii in range(len(list_code)):
                bybypara = {'code': list_code[ii], 'amount': 1, 'buysell': list_type[ii], 'kubun': '決済','nari_hiki': '', 'settle': -1, 'comment': list_code[ii] + '_' + list_type[ii] + '決済'}
                f02_gmo.gmo_cfd_exec(bybypara)

        if len(codes) > 0:
            self.send_msg += u'未決済銘柄あり_' + '_'.join([k for k in codes]) + "\n" + '_'.join([k for k in types]) + "\n" + '_'.join([k for k in amounts]) + "\n" + ok_msg
            for ii in range(len(codes)):
                code = codes[ii][:3] + '/' + codes[ii][3:]
                bybypara = {'code': code, 'amount': amounts[ii][:1], 'buysell': types[ii], 'kubun': '決済','nari_hiki': '', 'settle': -1, 'comment': codes[ii] + '_' + types[ii] + '決済'}
                f03_ctfx.f03_ctfx_main(bybypara)

    def main_TP(self):  #トラリピ
        dict_ww = {}
        code = '米NQ100'
        table_name = 'NQ100_TP'
        #情報取得
        dict_w = f02_gmo.info_get()
        dict_w = common.to_number(dict_w)
        sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': '_gmo_info'}
        sql_pd = common.select_sql('B05_cfd_stg.sqlite', sqls)
        dict_t = sql_pd.to_dict('records')
        dict_t = common.to_number(dict_t[0])
        dict_ww['H'] = max(dict_w[code + '_高'],dict_t[code + '_高'])
        dict_ww['L'] = min(dict_w[code + '_安'],dict_t[code + '_安'])
        dict_ww['C'] = dict_w[code]
        #前日の仕掛け情報取得
        sqls = "select *,rowid from %(table)s where rowid=(select max(rowid) from %(table)s) ;" % {'table': table_name}
        sql_pd = common.select_sql('B05_cfd_stg.sqlite', sqls)
        if len(sql_pd) == 0:
            common.insertDB3('B05_cfd_stg.sqlite', table_name, dict_ww)
            return
        dict_l = sql_pd.to_dict('records')
        dict_l = common.to_number(dict_l[0])
        sp_work =[]
        #決済確認
        if dict_l.get('poji'):
            sp_work = common.to_number(dict_l['poji'].split("_"))
            for i in reversed(range(len(sp_work))):
                if dict_ww['L'] > sp_work[i] + 100:
                    dict_ww['LongPL'] += 100
                    sp_work.pop(i)
            dict_ww['poji'] = "_".join([str(n) for n in sp_work])
            print(dict_ww)
        #前日トレード確認
        if dict_l.get('trade'):
            poji = []
            sp_work2 = common.to_number(dict_l['trade'].split("_"))
            if len(sp_work2) > 0:
                for i in reversed(range(len(sp_work2))):
                    if  dict_ww['H'] > sp_work2[i]:
                        print("追加",sp_work2[i] , dict_ww['L'])
                        sp_work.append(sp_work2[i])
                dict_ww['poji'] = "_".join([str(n) for n in sp_work])

        #仕掛け
        trade = []
        VAL = dict_ww['C'] - dict_ww['C'] % 100 + 100
        for ii in range(3):
            VVAL = VAL + 100 * ii
            if VVAL not in sp_work:
                trade.append(str(VVAL))
        dict_ww['trade'] = "_".join(trade)
        print(dict_ww)
        common.insertDB3('B05_cfd_stg.sqlite', table_name, dict_ww)

if __name__ == '__main__':  # 土曜日は5 datetime.datetime.now().weekday()
    info = e01_day_stg()
    argvs = sys.argv
    if argvs[1] == "daily_cfd":
        dict_w = f02_gmo.info_get()
        common.insertDB3('B05_cfd_stg.sqlite', '_gmo_info', dict_w)
        info.stg_main()
        info.cfd_poji_check()
        info.main_TP()  #トラリピ


    hours = datetime.datetime.now().hour
    minutes = datetime.datetime.now().minute
    if argvs[1] == "retry_check" and minutes > 30:
        info.retry_check() #20190218
        if minutes > 40:
            info.main_test(hours)

    common.mail_send(u'CFDトレード', info.send_msg)

    print("end", __file__)
