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

class profit:
    def __init__(self,num):
        self.num = num
        t = datetime.datetime.now()
        self.date = t.strftime("%Y%m%d%H%M%S")
        S_DIR = r"C:\data\90_profit\06_output"
        self.S_DIR = os.path.join(S_DIR,self.date + "_CFD")
        self.INPUT_DIR = r"C:\data\90_profit\05_input\CFD"

    #移動平均を基準とした上限・下限のブレイクアウト
    def breakout_ma_std(self,tsd,window,multi,para_val,para_key):
        #ub=moving average + std * multi
        #lb=moving average - std * multi
        #entry: long: s>ub; short: s<lb
        #exit: long:s<ma;  short: s>ma
        tsd.Close.dropna()
        m=tsd.Close.rolling(window).mean()
        m=m.shift(1)
        s=tsd.Close.rolling(window).std()
        s=s.shift(1)
#        print(tsd.Close)
        y=pd.concat([tsd.Close,m,s],axis=1).dropna()
#        y=pd.concat([tsd.Close,m,s]).dropna()
#        print(y)
        y.columns=['Close','ma_m','ma_s']
        y['ub']=y.ma_m+y.ma_s*multi
        y['lb']=y.ma_m-y.ma_s*multi
        y['pl']=0
        y['n']=0
#        BuyExit[N-2] = SellExit[N-2] = True #最後に強制エグジット
#        BuyPrice = SellPrice = 0.0 # 売買価格
        buy_key = para_key
        #sell_key = 1-para_key
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益
        #init----------------------------------
        n=0
        buy=0
        sell=0
        for i in range(1100,len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
#            if c<y.lb.iloc[i] and sell==0 and y[para_val].iloc[i] >= sell_key :#entry short-position
            if c<y.lb.iloc[i] and sell==0 and y.index[i].hour == para_key :#entry short-position
                sell=c
                y.iloc[i,6]=-1
            if c>y.ma_m.iloc[i] and sell!=0:#exit short-position
                y.iloc[i,5]=sell-c
                ShortPL[i] = sell-c #レポート用
                sell=0
#            if c>y.ub.iloc[i] and buy==0 and y[para_val].iloc[i] <= buy_key:#entry short-position
            if c>y.ub.iloc[i] and buy==0 and y.index[i].hour == para_key:#entry short-position
                buy=c
                y.iloc[i,6]=1
            if c<y.ma_m.iloc[i] and buy!=0:#exit short-position
                y.iloc[i,5]=c-buy
                LongPL[i] = c-buy #レポート用
                buy=0
            SumPL[i]=SumPL[i]+ShortPL[i]+LongPL[i] #レポート用
        return pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

    #過去の高値・安値を用いたブレイクアウト戦略
    def breakout_simple(self,tsd,window0,window9,para_val,para_key):
        #ub0=max - n0 days
        #lb0=min - n0 days
        #ub9=max - n9 days
        #lb9=min - n9 days

        y=tsd.dropna()
        y['ub0']=y['Close'].rolling(window0).max().shift(1)
        y['lb0']=y['Close'].rolling(window0).min().shift(1)
        y['ub9']=y['Close'].rolling(window9).max().shift(1)
        y['lb9']=y['Close'].rolling(window9).min().shift(1)
        y['pl']=0
        y['n']=0
        y=y.dropna()
        buy_key = para_key
        #sell_key = 1-para_key
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益

        #init----------------------------------
        n=0
        buy=0
        sell=0
        for i in range(1100,len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
            if c<y.lb0.iloc[i] and sell==0 and y.index[i].hour == para_key:#entry short-position
#            if c<y.lb0.iloc[i] and sell==0 and y[para_val].iloc[i] >= sell_key:#entry short-position
                sell=c
                y.iloc[i,6]=-1
            if c>y.ub9.iloc[i] and sell!=0:#exit short-position
                y.iloc[i,5]=sell-c
                ShortPL[i] = sell-c #レポート用
                sell=0
            if c>y.ub0.iloc[i] and buy==0 and y.index[i].hour == para_key:#entry short-position
#            if c>y.ub0.iloc[i] and buy==0 and y[para_val].iloc[i] <= buy_key:#entry short-position
                buy=c
                y.iloc[i,6]=1
            if c<y.lb9.iloc[i] and buy!=0:#exit short-position
                y.iloc[i,5]=c-buy
                LongPL[i] = c-buy #レポート用
                buy=0
            SumPL[i]=SumPL[i]+ShortPL[i]+LongPL[i] #レポート用
        return pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

    #フィルター付き高値・安値のブレイクアウト
    def breakout_simple_f(self,tsd,window0,window9,f0,f9,para_val,para_key):
        #ub0=max - n0 days
        #lb0=min - n0 days
        #ub9=max - n9 days
        #lb9=min - n9 days
        #filter long - f0 days
        #filter short - f9 days
        y=tsd.dropna()
        y['ub0']=y['Close'].rolling(window0).max().shift(1)
        y['lb0']=y['Close'].rolling(window0).min().shift(1)
        y['ub9']=y['Close'].rolling(window9).max().shift(1)
        y['lb9']=y['Close'].rolling(window9).min().shift(1)
        y['f0']=y['Close'].rolling(f0).mean().shift(1)
        y['f9']=y['Close'].rolling(f9).mean().shift(1)
        y['pl']=0
        y['n']=0
        y=y.dropna()
        buy_key = para_key
        #sell_key = 1-para_key
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益

        #init----------------------------------
        n=0
        buy=0
        sell=0
        for i in range(1100,len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
            if c<y.lb0.iloc[i] and sell==0 and y.f9.iloc[i]>y.f0.iloc[i] and y.index[i].hour == para_key:#entry short-position
#            if c<y.lb0.iloc[i] and sell==0 and y.f9.iloc[i]>y.f0.iloc[i] and y[para_val].iloc[i] >= sell_key:#entry short-position
                sell=c
                y.iloc[i,8]=-1
            if c>y.ub9.iloc[i] and sell!=0:#exit short-position
                y.iloc[i,7]=sell-c
                ShortPL[i] = sell-c #レポート用
                sell=0
            if c>y.ub0.iloc[i] and buy==0 and y.f9.iloc[i]<y.f0.iloc[i] and y.index[i].hour == para_key:#entry short-position
#            if c>y.ub0.iloc[i] and buy==0 and y.f9.iloc[i]<y.f0.iloc[i] and y[para_val].iloc[i] <= buy_key:#entry short-position
                buy=c
                y.iloc[i,8]=1
            if c<y.lb9.iloc[i] and buy!=0:#exit short-position
                y.iloc[i,7]=c-buy
                LongPL[i] = c-buy #レポート用
                buy=0
            SumPL[i]=SumPL[i]+ShortPL[i]+LongPL[i] #レポート用
        return pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

    #クロスオーバー移動平均
    def breakout_ma_two(self,tsd,window0,window9,para_val,para_key):
        tsd.Close.dropna()
        m0=tsd.Close.rolling(window0).mean().shift(1)
        m9=tsd.Close.rolling(window9).mean().shift(1)
#        y=pd.concat([tsd.Close,tsd[para_key],m0,m9],axis=1).dropna()
        y=pd.concat([tsd.Close,m0,m9],axis=1).dropna()
        y.columns=['Close','ma0','ma9']
        y['pl']=0
        y['n']=0
        buy_key = para_key
        #sell_key = 1-para_key
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益

        #init----------------------------------
        n=0
        buy=0
        sell=0
        for i in range(1100,len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            m0=y.ma0.iloc[i]
            m9=y.ma9.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
            if m0<m9 and sell==0 and y.index[i].hour == para_key:#entry short-position
#            if m0<m9 and sell==0 and y[para_val].iloc[i] >= sell_key:#entry short-position
                sell=c
                y.iloc[i,4]=-1
            if m0>m9 and sell!=0:#exit short-position
                y.iloc[i,3]=sell-c
                ShortPL[i] = sell-c #レポート用
                sell=0
            if m0>m9 and buy==0 and y.index[i].hour == para_key:#entry short-position
#            if m0>m9 and buy==0 and y[para_val].iloc[i] <= buy_key:#entry short-position
                buy=c
                y.iloc[i,4]=1
            if m0<m9 and buy!=0:#exit short-position
                y.iloc[i,3]=c-buy
                LongPL[i] = c-buy #レポート用
                buy=0
            SumPL[i]=SumPL[i]+ShortPL[i]+LongPL[i] #レポート用
        return pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

    #3つの移動平均を使った戦略
    def breakout_ma_three(self,tsd,window0,window9,window5,para_val,para_key):
        tsd.Close.dropna()
        m0=tsd.Close.rolling(window0).mean().shift(1)
        m9=tsd.Close.rolling(window9).mean().shift(1)
        m5=tsd.Close.rolling(window5).mean().shift(1)
        y=pd.concat([tsd.Close,m0,m9,m5],axis=1)
        y.columns=['Close','ma0','ma9','ma5']
#        y=pd.concat([tsd.Close,tsd[para_val],m0,m9,m5],axis=1).dropna()
#        y.columns=['Close',para_val,'ma0','ma9','ma5']
        y['pl']=0
        y['n']=0
        buy_key = para_key
        #sell_key = 1-para_key
        #レポート用
        N = len(y) #FXデータのサイズ
        LongPL = np.zeros(N) # 買いポジションの損益
        ShortPL = np.zeros(N) # 売りポジションの損益
        SumPL = np.zeros(N) # 売りポジションの損益

        #init----------------------------------
        n=0
        buy=0
        sell=0
        for i in range(1100,len(y)):
            da=y.index[i]
            c=y.Close.iloc[i]
            m0=y.ma0.iloc[i]
            m9=y.ma9.iloc[i]
            m5=y.ma5.iloc[i]
            SumPL[i]=SumPL[i-1] #レポート用
            if sell==0 and m0<m9 and m0<m5 and m9<m5 and y.index[i].hour == para_key:#entry short-position
#            if sell==0 and m0<m9 and m0<m5 and m9<m5 and y[para_val].iloc[i] >= sell_key:#entry short-position
                sell=c
                y.iloc[i,5]=-1
            if (m0>m9 and sell!=0) or (m0>m5 and sell!=0) or (m9>m5 and sell!=0):#exit short-position
                y.iloc[i,4]=sell-c
                ShortPL[i] = sell-c #レポート用
                sell=0
            if buy==0 and m0>m9 and m0>m5 and m9>m5 and y.index[i].hour == para_key:#entry short-position
#            if buy==0 and m0>m9 and m0>m5 and m9>m5 and y[para_val].iloc[i] <= buy_key:#entry short-position
                buy=c
                y.iloc[i,5]=1
            if (m0<m9 and buy!=0) or (m0<m5 and buy!=0) or (m9<m5 and buy!=0):#exit short-position
                y.iloc[i,4]=c-buy
                LongPL[i] = c-buy #レポート用
                buy=0
            SumPL[i]=SumPL[i]+ShortPL[i]+LongPL[i] #レポート用
        return pd.DataFrame({'LongPL':LongPL, 'ShortPL':ShortPL,'Sum':SumPL}, index=y.index)

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

    def csv_connect(slef,dir,key):
        all = []
        flag = 0
        for root, dirs, files in os.walk(dir):
            for fname in files:
                filename = os.path.join(root, fname)
                if filename.count(key):
#                    print(filename)
#                    temp = pd.read_csv(filename,engine='python',index_col=0,parse_dates=True,encoding=common.check_encoding(filename),skiprows=1).iloc[:,0:4]
                    temp = pd.read_csv(filename,engine='python',index_col=0,parse_dates=True,encoding=common.check_encoding(filename),skiprows=1).iloc[:,0:4]
                    temp.columns = ["Open","High","Low","Close"]
                    temp.index_label='date'
                    if flag == 0:
                        flag = 1
                        all = temp
                    else:
                        all = pd.concat([all,temp])

        return all
    def interval(self,all,priod):
        a = all.resample(priod).first()
        return a
    def save_to_csv(self,save_name,title,backreport):
        #ヘッダー追加
        if os.path.exists(save_name) == False:
            dic_name = ",".join([str(k[0]).replace(",","")  for k in backreport.items()])+"\n"
            with open(save_name, 'w') as f:
                f.write("now,stockname,"+dic_name)
        #1列目からデータ挿入
        dic_val = ",".join([str(round(k[1],3)).replace(",","")  for k in backreport.items()])+"\n"
        with open(save_name, 'a', encoding="utf-8") as f:
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


    def byby(self,val):
        ddd = 0
        return 0



    #移動平均を基準とした上限・下限のブレイクアウト
    def breakout_ma_daily(self,tsd,windows1,windows2,windows3,windows4):
        y = tsd.dropna()
        y['ma_m']=round(y.Close.rolling(windows1).mean().shift(1),0)
        y['ma_s']=round(y.Close.rolling(windows2).mean().shift(1),0)
        y['up10']=round(y.Close.rolling(windows3).max().shift(1),0)
        y['down10'] = round(y.Close.rolling(windows4).min().shift(1), 0)
        y['stop'] = round((y.Close.rolling(3).max() -
                           y.Close.rolling(3).min()).shift(1), 0) * 3
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
            SumPL[i]=SumPL[i-1] #レポート用
            if sell != 0 or buy != 0:
                y.iloc[i,6] = y.iloc[i-1,6]
                if buy != 0 and stop < y.stopL.iloc[i]:
                    stop = y.stopL.iloc[i]
                if sell != 0 and stop > y.stopS.iloc[i]:
                    stop = y.stopS.iloc[i]
            y.iloc[i,8] = y.iloc[i-1,8]

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
        return y, pd.DataFrame({'LongPL': LongPL, 'ShortPL': ShortPL, 'Sum': SumPL}, index=y.index)

    def main_exec(self):
        save_name = os.path.join(self.S_DIR, "all_report_FX.csv")
        os.mkdir(str(self.S_DIR))
        """
        code_list=['dow30']
        for code in code_list:
#            tsd = pd.read_csv(os.path.join(self.INPUT_DIR ,code + '.csv'),index_col=0,parse_dates=True)
            tsd = pd.read_csv(os.path.join(
                self.INPUT_DIR, code + '.csv'), index_col=0, parse_dates=True).dropna()
        """
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


            for i in range(2,100,10):
                windows1 = i
                for ii in range(2, 100, 10):
                    windows2 = ii
                    for iii in range(2, 100, 10):
                        windows3 = iii
                        for iiii in range(2, 100, 10):
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
#                                y.pl.cumsum().plot()
#                                plt.show()
                            if Equity != 0:
                                self.save_to_csv(save_name, code + title + "_breakout_daily", backreport)
#                                PL.to_csv(os.path.join(
#                                    self.S_DIR, code + title + '_breakout_daily_dital.csv'))


if __name__ == "__main__":
    info = profit(0)
#    info.main_exec()
    col = 0.1
    save_name = os.path.join(info.S_DIR,"all_report_FX.csv")
    if os.path.exists(save_name):
        os.remove(save_name)
    os.mkdir(str(info.S_DIR))
    #日付インデックス作成
    df = pd.DataFrame(index=pd.date_range(
        '2007/01/01', common.env_time()[1][0:10]))
    df = df.join(pd.read_csv(os.path.join(info.INPUT_DIR, 'SP500.csv'),
                                index_col=0, parse_dates=True, encoding="cp932"))
    df = df.dropna()
    title = list(df.columns)
    for code in title:
        print(code)
        tsd = pd.DataFrame(df[code], index=df.index)
        tsd.columns = ["Close"]
        tsd[["Close"]] = tsd[["Close"]].astype(float)

        print("1")
        for i in range(2,101,5):
#                window=350
#                multi=2.5
            window=i
            multi=2.5

            PL = info.breakout_ma_std(tsd, window, multi, col, 0)
#                print(PL.index.max())
#                print("AAAA",int(PL.iloc[-1]['ShortPL']))
#                exit()
#                PL.to_csv("EXT.CSV")
            print("AAAA", int(PL.iloc[-1]['ShortPL']),int(PL.iloc[-1]['LongPL']),int(PL.iloc[-1]['Sum']))
            print("AAAA", PL['ShortPL'].min(),PL['LongPL'].min(),int(PL.iloc[-1]['Sum']))

            Equity , backreport=info.BacktestReport(PL)
            if Equity != 0:
                info.save_to_csv(save_name, code + str(i) +
                                "_1BacktestReport", backreport)
                PL.to_csv(os.path.join(info.S_DIR, code +
                                    "_" + str(i) + '_1BacktestReport_dital.csv'))

        print("2")
        for i in range(2,101,5):
            window0=i
            for ii in range(2,101,5):
                window9 = ii
                title = "_" + str(i) + "_" + str(ii)
                PL=info.breakout_simple(tsd,window0,window9,col,0)
                Equity, backreport = info.BacktestReport(PL)
                if Equity != 0:
                    info.save_to_csv(save_name, code + title +
                                    "_2breakout_simple", backreport)
                    PL.to_csv(os.path.join(info.S_DIR, code +
                                        title  + '_2breakout_simple_dital.csv'))
            print("AAAA2", PL['ShortPL'].min(),PL['LongPL'].min(),int(PL.iloc[-1]['Sum']))


        print("3")
        for i in range(2,101,5):
            window0 = i
            for ii in range(2,101,5):
                window9 = ii
                for iii in range(2,101,5):
                    f0 = iii
                    for iiii in range(2,101,5):
                        f9 = iiii
                        title = "_" + str(i) + "_" + str(ii) + str(iii) + "_" + str(iiii)

                        PL=info.breakout_simple_f(tsd,window0,window9,f0,f9,col,0)
                        Equity, backreport = info.BacktestReport(PL)
                        if Equity != 0:
                            info.save_to_csv(save_name, code + title +
                                            "_3breakout_simple_f", backreport)
                            PL.to_csv(os.path.join(info.S_DIR,code + title + '_3breakout_simple_f_dital.csv'))

        print("4")
        for i in range(2,101,5):
            window0 = i
            for ii in range(2,101,5):
                window9 = ii
                title = "_" + str(i) + "_" + str(ii)
                PL=info.breakout_ma_two(tsd,window0,window9,col,0)
                Equity, backreport = info.BacktestReport(PL)
                if Equity != 0:
                    info.save_to_csv(save_name, code + title +
                                    "_4breakout_ma_two", backreport)
                    PL.to_csv(os.path.join(info.S_DIR,code + title + '_4breakout_ma_two.csv'))
            print("AAAA4", PL['ShortPL'].min(),PL['LongPL'].min(),int(PL.iloc[-1]['Sum']))

        print("5")
        for i in range(2,101,5):
            window0 = i
            for ii in range(2,101,5):
                window9 = ii
                for iii in range(2,101,5):
                    window5 = iii
                    title = "_" + str(i) + "_" + str(ii) + "_" + str(iii)
                    PL=info.breakout_ma_three(tsd,window0,window9,window5,col,0)
                    Equity, backreport = info.BacktestReport(PL)
                    if Equity != 0:
                        info.save_to_csv(save_name,code+ str(i)+"_5breakout_ma_three",backreport)
                        PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_5breakout_ma_three.csv'))
        print("AAAA5", PL['ShortPL'].min(),PL['LongPL'].min(),int(PL.iloc[-1]['Sum']))


    #            詳細調査の場合
    #            all_ = pd.concat([tsd,axis=1)
    #            all_.to_csv(code + 'dital.csv' )



#        except:
#            pass
    import shutil
    shutil.copy2(__file__, info.S_DIR)


#    print("end",__file__)
