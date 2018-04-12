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
from pandas.tools.plotting import scatter_matrix
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

    def BacktestReport(self, PL):
        backreport = {'総利益':"", '総損失':"", '総損益':"", 'プロフィットファクター':"", '平均損益':"", '最大ドローダウン':"", 'リカバリーファクター':"",
        '★総トレード数':"", '勝トレード数':"", '最大勝トレード':"", '平均勝トレード':"", '負トレード数':"", '最大負トレード':"", '平均負トレード':"", '勝率':"",
        '★買いトレード数':"", 'buy勝トレード数':"", 'buy負トレード数':"", 'buy勝率':"", 'buy勝トレード利益':"", 'buy負トレード利益':"", 'buy合計損益':"", 'buyプロフィットファクター':"",
        '★売りトレード数':"", 'sell勝トレード数':"", 'sell負トレード数':"", 'sell勝率':"", 'sell勝トレード利益':"", 'sell負トレード利益':"", 'sell合計損益':"", 'sellプロフィットファクター':""}
#        if int(PL.iloc[-1]['ShortPL']) == 0 or int(PL.iloc[-1]['LongPL']) == 0:
#            return 0, backreport
        print(PL['ShortPL'].min(), PL['LongPL'].min(), PL['ShortPL'].max(), PL['LongPL'].max())
        if 0.0 in (PL['ShortPL'].min(), PL['LongPL'].min(), PL['ShortPL'].max(), PL['LongPL'].max()):
            return 0, backreport
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
        backreport['buyプロフィットファクター'] = round( - LongPL.clip_lower(0).sum() / LongPL.clip_upper(0).sum(), 2)

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
        backreport['sellプロフィットファクター'] = round(-ShortPL.clip_lower(0).sum()/ShortPL.clip_upper(0).sum(), 2)

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
        backreport['平均勝トレード'] = round((LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum())/WinTrades, 2)
        backreport['負トレード数'] = LoseTrades
        backreport['最大負トレード'] = min(LongPL.min(), ShortPL.min())
        backreport['平均負トレード'] = round((LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum())/LoseTrades, 2)
        backreport['勝率'] = round(WinTrades/Trades*100, 2)

        GrossProfit = LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum()
        GrossLoss = LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum()

        Profit = GrossProfit+GrossLoss
        Equity = (LongPL + ShortPL).sum()
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

        return Equity,backreport

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
    def breakout_ma_daily(self,tsd,windows1,windows2,windows3,windows4):
        y = tsd.dropna()
#        y = y.Series([Close],dtype = int64)
#        print(y.Close.dtype)
        y['ma_m'] = round(y.Close.rolling(windows1).mean().shift(1), 0)
        y['ma_s'] = round(y.Close.rolling(windows2).mean().shift(1), 0)
        y['up10'] = round(y.Close.rolling(windows3).max().shift(1), 0)
        y['down10'] = round(y.Close.rolling(windows4).min().shift(1), 0)
        y['stop'] = round((y.Close.rolling(3).max() -
                           y.Close.rolling(3).min()).shift(1), 0) * 3

        y['stop'] = (y.Close.rolling(3).max() - y.Close.rolling(3).min()).shift(1) * 5
        y['n'] = 0
        y['pl'] = 0
        y['allsum'] = 0
        y['stopL'] = y.Close - y['stop']
        y['stopS'] = y.Close + y['stop']

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
            clast=y.Close.iloc[i-3]
            SumPL[i]=SumPL[i-1] #レポート用
            if sell != 0 or buy != 0:
                y.iloc[i, 6] = y.iloc[i-1, 6]
            if buy != 0 and stop < y.stopL.iloc[i]:
                stop = y.stopL.iloc[i]
            if sell != 0 and stop > y.stopS.iloc[i]:
                stop = y.stopS.iloc[i]
            y.iloc[i, 8] = y.iloc[i-1, 8]

            # entry short-position
            if y.ma_m.iloc[i] > y.ma_s.iloc[i] and y.down10.iloc[i] > c and sell == 0 and c < y.ma_s.iloc[i] and y.iloc[i, 6] == 0:
                sell = c
                y.iloc[i, 6] = -1
                stop = y.stopS.iloc[i]
#            elif c > y.ma_s.iloc[i] and sell != 0:  # exit short-position
            elif c > stop and sell != 0:  # exit short-positiony['stopL']
                y.iloc[i, 6] = 0
                y.iloc[i, 7] = sell-c
                y.iloc[i, 8] += y.iloc[i, 7]
                ShortPL[i] = sell-c  # レポート用
                sell = 0
            # entry short-position
            elif y.ma_m.iloc[i] < y.ma_s.iloc[i] and y.up10.iloc[i] < c and buy == 0 and c > y.ma_s.iloc[i] and y.iloc[i, 6] == 0:
                buy = c
                y.iloc[i, 6] = 1
                stop = y.stopL.iloc[i]
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
        save_name = os.path.join(self.S_DIR,"all_report_FX.csv")
        os.mkdir(str(self.S_DIR))

        #日付インデックス作成
        df = pd.DataFrame(index=pd.date_range(
            '2007/01/01', common.env_time()[1][0:10]))
        df = df.join(pd.read_csv(os.path.join(self.INPUT_DIR, 'SP500.csv'),
                                 index_col=0, parse_dates=True, encoding="cp932"))
        df = df.dropna()
        title = list(df.columns)
        for code in title:
            print(code)
            tsd = pd.DataFrame(df[code], index=df.index)
            tsd.columns = ["Close"]
            tsd[["Close"]] = tsd[["Close"]].astype(float)

#        y = y.Series([Close],dtype = int64)
#        print(y.Close.dtype)


            ###追加
            title = "_" + str(100) + "_" + str(50) + "_" + str(50) + "_" + str(50)
            y,PL = self.breakout_ma_daily(tsd,100,50,30,20)
            Equity, backreport = self.BacktestReport(PL)
            print(title, int(
                PL.iloc[-1]['ShortPL']), int(PL.iloc[-1]['LongPL']), int(PL.iloc[-1]['Sum']),Equity)
            if PL.iloc[-1]['Sum'] != 0:
                PL.to_csv(os.path.join(
                    self.S_DIR, code + title + '_breakout_daily_dital.csv'))
                y.to_csv(os.path.join(
                    self.S_DIR, code + title + '_breakout_daily_dital_all.csv'))
#                                y.pl.cumsum().plot()
#                                plt.show()
            if Equity != 0:
                self.save_to_csv(save_name, code + title + "_breakout_daily", backreport)
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
                            title = "_" + str(i) + "_" + str(ii) + "_" + str(iii) + "_" + str(iiii)
                            y,PL = self.breakout_ma_daily(tsd,windows1,windows2,windows3,windows4)
                            Equity, backreport = self.BacktestReport(PL)
                            print(title, int(
                                PL.iloc[-1]['ShortPL']), int(PL.iloc[-1]['LongPL']), int(PL.iloc[-1]['Sum']),Equity)
                            if PL.iloc[-1]['Sum'] != 0:
                                PL.to_csv(os.path.join(
                                    self.S_DIR, code + title + '_breakout_daily_dital.csv'))
                                y.to_csv(os.path.join(
                                    self.S_DIR, code + title + '_breakout_daily_dital_all.csv'))
#                                y.pl.cumsum().plot()
#                                plt.show()
                            if Equity != 0:
                                self.save_to_csv(save_name, code + title + "_breakout_daily", backreport)
#                                PL.to_csv(os.path.join(
#                                    self.S_DIR, code + title + '_breakout_daily_dital.csv'))
            """

if __name__ == "__main__":
    info = profit(0)
    info.main_exec()
    shutil.copy2(__file__, info.S_DIR)


    print("end",__file__)