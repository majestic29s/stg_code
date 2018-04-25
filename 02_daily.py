#!/usr/bin/env python
# -*- coding: utf-8 -*-
#%matplotlib inline
import pandas_datareader.data as web
import numpy as np
#import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
import pandas.tseries as pdt
from datetime import date
#import seaborn as sns
import common
import datetime
import os,csv
import shutil

class profit:
    def __init__(self,num):
        self.num = num
        t = datetime.datetime.now()
        self.date = t.strftime("%Y%m%d%H%M%S")
        S_DIR = r"C:\data\90_profit\06_output"
        self.S_DIR = os.path.join(S_DIR,self.date + "_CFD")
        self.INPUT_DIR = r"C:\data\90_profit\05_input\CFD"
        self.save_name = os.path.join(self.S_DIR, "all_report_FX.csv")
        if os.path.exists(self.save_name):
            os.remove(self.save_name)
        os.mkdir(str(self.S_DIR))
        shutil.copy2(__file__, self.S_DIR)

    def BacktestReport(self, PL, title):
        backreport = {'総利益': "", '総損失': "", '総損益': "", 'プロフィットファクター': "", '平均損益': "", '最大ドローダウン': "", 'リカバリーファクター': "",
                      '★総トレード数': "", '勝トレード数': "", '最大勝トレード': "", '平均勝トレード': "", '負トレード数': "", '最大負トレード': "", '平均負トレード': "", '勝率': "",
                      '★買いトレード数': "", 'buy勝トレード数': "", 'buy負トレード数': "", 'buy勝率': "", 'buy勝トレード利益': "", 'buy負トレード利益': "", 'buy合計損益': "", 'buyプロフィットファクター': "",
                      '★売りトレード数': "", 'sell勝トレード数': "", 'sell負トレード数': "", 'sell勝率': "", 'sell勝トレード利益': "", 'sell負トレード利益': "", 'sell合計損益': "", 'sellプロフィットファクター': ""}

        #大きな利益損益除外フィルター
        tmp1 = max(abs(PL['ShortPL']) + abs(PL['LongPL']))
#        tmp2 = min(PL['ShortPL'] + PL['LongPL'])
        tmp3 = (PL['ShortPL'] + PL['LongPL']).sum()
        if tmp3 / tmp1 <3:
            return 0, backreport

        #0を除去
        if 0 in (PL['LongPL'].clip_lower(0).sum(), PL['LongPL'].clip_upper(0).sum(), PL['ShortPL'].clip_lower(0).sum(), PL['ShortPL'].clip_upper(0).sum()):
            return 0, backreport

        #角度確認
        l1 = int(len(PL) * 0.25)
        l2 = int(len(PL) * 0.5)
        l3 = int(len(PL) * 0.75)

        if PL.iloc[0]['Sum'] < PL.iloc[l1]['Sum'] < PL.iloc[l2]['Sum'] < PL.iloc[l3]['Sum'] < PL.iloc[-1]['Sum']:
            pass
        elif PL.iloc[0]['Sum'] > PL.iloc[l1]['Sum'] > PL.iloc[l2]['Sum'] > PL.iloc[l3]['Sum'] > PL.iloc[-1]['Sum']:
            pass
        else:
            return 0, backreport
        print(title, PL['ShortPL'].min(), PL['LongPL'].min(),
              PL['ShortPL'].max(), PL['LongPL'].max())

        LongPL = PL['LongPL']
        LongTrades = np.count_nonzero(PL['LongPL'])
        LongWinTrades = np.count_nonzero(LongPL.clip_lower(0))
        LongLoseTrades = np.count_nonzero(LongPL.clip_upper(0))
        if LongTrades == 0:
            LongTrades = 1
        if LongWinTrades == 0:
            LongWinTrades = 1
        if LongLoseTrades == 0:
            LongLoseTrades = 1

        backreport['★買いトレード数'] = LongTrades
        backreport['buy勝トレード数'] = LongWinTrades
        backreport['buy負トレード数'] = LongLoseTrades
        backreport['buy勝率'] = round(LongWinTrades/LongTrades*100, 2)
        backreport['buy勝トレード利益'] = round(LongPL.clip_lower(0).sum(), 4)
        backreport['buy負トレード利益'] = round(LongPL.clip_upper(0).sum(), 4)
        backreport['buy合計損益'] = round(LongPL.sum() / LongTrades, 4)
        backreport['buyプロフィットファクター'] = round(
            - LongPL.clip_lower(0).sum() / LongPL.clip_upper(0).sum(), 2)

        ShortPL = PL['ShortPL']
        ShortTrades = np.count_nonzero(PL['ShortPL'])
        ShortWinTrades = np.count_nonzero(ShortPL.clip_lower(0))
        ShortLoseTrades = np.count_nonzero(ShortPL.clip_upper(0))
        if ShortTrades == 0:
            ShortTrades = 1
        if ShortWinTrades == 0:
            ShortWinTrades = 1
        if ShortLoseTrades == 0:
            ShortLoseTrades = 1

        backreport['★売りトレード数'] = ShortTrades
        backreport['sell勝トレード数'] = ShortWinTrades
        backreport['sell負トレード数'] = ShortLoseTrades
        backreport['sell勝率'] = round(ShortWinTrades/ShortTrades*100, 2)
        backreport['sell勝トレード利益'] = round(ShortPL.clip_lower(0).sum(), 4)
        backreport['sell負トレード利益'] = round(ShortPL.clip_upper(0).sum(), 4)
        backreport['sell合計損益'] = round(ShortPL.sum()/ShortTrades, 4)
        backreport['sellプロフィットファクター'] = round(
            -ShortPL.clip_lower(0).sum()/ShortPL.clip_upper(0).sum(), 2)

        Trades = LongTrades + ShortTrades
        WinTrades = LongWinTrades+ShortWinTrades
        LoseTrades = LongLoseTrades+ShortLoseTrades
        if Trades == 0:
            Trades = 1
        if WinTrades == 0:
            WinTrades = 1
        if LoseTrades == 0:
            LoseTrades = 1

        backreport['★総トレード数'] = Trades
        backreport['勝トレード数'] = WinTrades
        backreport['最大勝トレード'] = max(LongPL.max(), ShortPL.max())
        backreport['平均勝トレード'] = round(
            (LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum())/WinTrades, 2)
        backreport['負トレード数'] = LoseTrades
        backreport['最大負トレード'] = min(LongPL.min(), ShortPL.min())
        backreport['平均負トレード'] = round(
            (LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum())/LoseTrades, 2)
        backreport['勝率'] = round(WinTrades/Trades*100, 2)

        GrossProfit = LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum()
        GrossLoss = LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum()

        Profit = GrossProfit+GrossLoss
#        MDD = (Equity.max()-Equity).max()
        backreport['総利益'] = round(GrossProfit, 4)
        backreport['総損失'] = round(GrossLoss, 4)
        backreport['総損益'] = round(Profit, 4)
        backreport['プロフィットファクター'] = round(-GrossProfit/GrossLoss, 4)
        backreport['平均損益'] = round(Profit/Trades, 4)
#        backreport['最大ドローダウン'] = round(MDD, 4)
#        backreport['リカバリーファクター'] = round(Profit/MDD, 4)
        backreport['最大ドローダウン'] = 0
        backreport['リカバリーファクター'] = 0
        if 0.7 < backreport['プロフィットファクター'] < 1.2 and backreport['★総トレード数'] < 50:
            return
        print("Report_Write!!!",title)
        self.save_to_csv(self.save_name, title, backreport)
        PL.to_csv(os.path.join(self.S_DIR, title))

    def interval(self,all,priod):
        a = all.resample(priod).first()
        return a
    def save_to_csv(self,save_name,title,backreport):
        #ヘッダー追加
        if os.path.exists(save_name) == False:
            dic_name = ",".join([str(k[0]).replace(",","")  for k in backreport.items()])+"\n"
            with open(save_name, 'w', encoding="cp932") as f:
                f.write("now,stockname,"+dic_name)
        #1列目からデータ挿入
        dic_val = ",".join([str(round(k[1],3)).replace(",","")  for k in backreport.items()])+"\n"
        with open(save_name, 'a', encoding="cp932") as f:
            f.write(common.env_time()[1] +"," + title+","+dic_val)
    def priod_edit(self,tsd,priod):
            #       ５分間隔のデータ作成
            o = tsd.Close.resample(priod).first().dropna()
            h = tsd.Close.resample(priod).max().dropna()
            l = tsd.Close.resample(priod).min().dropna()
            c = tsd.Close.resample(priod).last().dropna()
            tsd = pd.concat([o,h,l,c],axis=1)
            tsd.columns = ["Open","High","Low","Close"]
            #乖離平均追加
            for t in [7,30,200,1000]:
#                h=tsd['High'].rolling(t).max().shift(1)
#                l=tsd['Low'].rolling(t).min().shift(1)
#                c=tsd['Close'].shift(1)
                tsd['rng'+str(t)]=round((tsd['Close'].shift(1)-tsd['Low'].rolling(t).min().shift(1))/(tsd['High'].rolling(t).max().shift(1)-tsd['Low'].rolling(t).min().shift(1)),2)
                tsd['avg'+str(t)]=round(tsd['Close'].shift(1)/tsd['Close'].rolling(t).mean().shift(1)-1,2)
            return tsd





    #移動平均を基準とした上限・下限のブレイクアウト
    def breakout_ma_daily(self,tsd,windows1,windows2,windows3,windows4,para):
        y = tsd.dropna()
#        y = y.Series([Close],dtype = int64)
#        print(y.Close.dtype)
        y['ma_m'] = round(y.Close.rolling(windows1).mean().shift(1), 0)
        y['ma_s'] = round(y.Close.rolling(windows2).mean().shift(1), 0)
        y['up10'] = round(y.Close.rolling(windows3).max().shift(1), 0)
        y['down10'] = round(y.Close.rolling(windows4).min().shift(1), 0)

        y['n'] = 0
        y['pl'] = 0
        y['allsum'] = 0
        y['stop'] = (y.Close.rolling(3).max() - y.Close.rolling(3).min()).shift(1) * 5
        y['stopL'] = y.Close - y['stop']
        y['stopS'] = y.Close + y['stop']
        y['idx1'] = y.Close.rolling(para).mean().shift(1)
        y['idx2'] = y.idx.rolling(para).mean().shift(1)
        y['idx'] = y['idx1'] / y['idx2']
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益

        #init----------------------------------
        n=0
        buy=0
        sell=0
        stop = 0
        for i in range(len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
            if buy != 0 and stop < y.iloc[i, 10]:
                stop = y.iloc[i, 10]
            if sell != 0 and stop > y.iloc[i, 11]:
                stop = y.iloc[i, 11]
            y.iloc[i, 6] = y.iloc[i-1, 6]
            y.iloc[i, 8] = y.iloc[i-1, 8]

            # entry short-position
#            if y.ma_m.iloc[i] > y.ma_s.iloc[i] and y.down10.iloc[i] > c and sell == 0 and y.idx.iloc[i] < 1:
            if y.ma_m.iloc[i] > y.ma_s.iloc[i] and y.down10.iloc[i] > c and sell == 0:

                sell = c
                y.iloc[i, 6] = -1
                stop = y.iloc[i, 11]
#            elif c > y.ma_s.iloc[i] and sell != 0:  # exit short-position
            elif c > stop and sell != 0:  # exit short-positiony['stopL']
                y.iloc[i, 6] = 0
                y.iloc[i, 7] = sell-c
                y.iloc[i, 8] += y.iloc[i, 7]
                ShortPL[i] = sell-c  # レポート用
                sell = 0
            # entry short-position
#            elif y.ma_m.iloc[i] < y.ma_s.iloc[i] and y.up10.iloc[i] < c and buy == 0 and y.idx.iloc[i] > 1:
            elif y.ma_m.iloc[i] < y.ma_s.iloc[i] and y.up10.iloc[i] < c and buy == 0:
                buy = c
                y.iloc[i, 6] = 1
                stop = y.iloc[i, 10]
#            elif c < y.ma_s.iloc[i] and buy != 0:  # exit short-position
            elif c < stop and buy != 0:  # exit short-position
                y.iloc[i, 6] = 0
                y.iloc[i, 7] = c - buy
                y.iloc[i, 8] += y.iloc[i, 7]
                LongPL[i] = c-buy  # レポート用
                buy = 0
            SumPL[i] = SumPL[i]+ShortPL[i]+LongPL[i]  # レポート用
        return y,pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

    def main_exec(self):
        #日付インデックス作成
        df = pd.DataFrame(index=pd.date_range(
            '2007/01/01', common.env_time()[1][0:10]))
        df = df.join(pd.read_csv(os.path.join(self.INPUT_DIR, 'SP500.csv'),
                                 index_col=0, parse_dates=True, encoding="cp932"))
        df = df.dropna()
        colname = list(df.columns)
#        colname = ['白金スポット','原油']
        for code in colname:
            for code_idx in colname:
                if code == code_idx:
                    continue
                tsd = pd.DataFrame(df[[code,code_idx]], index=df.index)
                tsd.columns = ["Close","idx"]
                tsd[["Close","idx"]] = tsd[["Close","idx"]].astype(float)
                """
                ###追加
                title = code + "_" + str(100) + "_" + str(50) + "_" + str(50) + "_" + str(50) + ".csv"
                y,PL = self.breakout_ma_daily(tsd,10,2,10,5,100)
                y.to_csv(os.path.join(self.S_DIR, title))
                self.BacktestReport(PL,title)
                ###追加
                """
                for i in range(2,110,10):
                    windows1 = i
                    for ii in range(2, 110, 10):
                        windows2 = ii
                        for iii in range(2, 110, 10):
                            windows3 = iii
                            for iiii in range(2, 110, 10):
                                if i == ii or iii == iiii:
                                    break
                                windows4 = iiii
                                title = code + "_"+ code_idx + "_" + str(i) + "_" + str(ii) + "_" + str(iii) + "_" + str(iiii) + ".csv"
                                t = datetime.datetime.now()
                                y,PL = self.breakout_ma_daily(tsd,windows1,windows2,windows3,windows4,100)
                                self.BacktestReport(PL,title)
                                print(datetime.datetime.now() -
                                      t, title, self.date)

if __name__ == "__main__":
    info = profit(0)
    info.main_exec()

    print("end",__file__)
