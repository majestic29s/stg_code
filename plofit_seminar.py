#!/usr/bin/env python
# -*- coding: utf-8 -*-
#%matplotlib inline
import pandas_datareader.data as web
import numpy as np
#import statsmodels.api as sm
#import matplotlib.pyplot as plt
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
        self.S_DIR = os.path.join(S_DIR,self.date + "_FX")
        self.INPUT_DIR = r"C:\data\90_profit\05_input\FX"

    #移動平均を基準とした上限・下限のブレイクアウト
    def breakout_ma_std(self,tsd,window,multi,para_val,para_key):
        #ub=moving average + std * multi
        #lb=moving average - std * multi
        #entry: long: s>ub; short: s<lb
        #exit: long:s<ma;  short: s>ma
#        print(tsd)
        m=tsd.Close.rolling(window).mean().dropna()
        m=m.shift(1)
        s=tsd.Close.rolling(window).std()
        s=s.shift(1)
        y=pd.concat([tsd.Close,m,s],axis=1).dropna()
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
        m0=tsd.Close.rolling(window0).mean().shift(1).dropna()
        m9=tsd.Close.rolling(window9).mean().shift(1).dropna()
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
        m0=tsd.Close.rolling(window0).mean().shift(1).dropna()
        m9=tsd.Close.rolling(window9).mean().shift(1).dropna()
        m5=tsd.Close.rolling(window5).mean().shift(1).dropna()
        y=pd.concat([tsd.Close,m0,m9,m5],axis=1).dropna()
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

    def BacktestReport(self,PL):
        backreport = {'総利益':"", '総損失':"", '総損益':"", 'プロフィットファクター':"", '平均損益':"", '最大ドローダウン':"", 'リカバリーファクター':"",
        '★総トレード数':"", '勝トレード数':"", '最大勝トレード':"", '平均勝トレード':"", '負トレード数':"", '最大負トレード':"", '平均負トレード':"", '勝率':"",
        '★買いトレード数':"", 'buy勝トレード数':"", 'buy負トレード数':"", 'buy勝率':"", 'buy勝トレード利益':"", 'buy負トレード利益':"", 'buy合計損益':"", 'buyプロフィットファクター':"",
        '★売りトレード数':"", 'sell勝トレード数':"", 'sell負トレード数':"", 'sell勝率':"", 'sell勝トレード利益':"", 'sell負トレード利益':"", 'sell合計損益':"", 'sellプロフィットファクター':""}
        if int(PL.iloc[-1]['ShortPL']) == 0 or int(PL.iloc[-1]['LongPL']) == 0:
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
        backreport['buy合計損益'] = round(LongPL.sum()/LongTrades, 4)
        backreport['buyプロフィットファクター'] = round(-LongPL.clip_lower(0).sum()/LongPL.clip_upper(0).sum(), 2)

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
        Equity = (LongPL+ShortPL).sum()
        MDD = (Equity.max()-Equity).max()
        backreport['総利益'] = round(GrossProfit, 4)
        backreport['総損失'] = round(GrossLoss, 4)
        backreport['総損益'] = round(Profit, 4)
        backreport['プロフィットファクター'] = round(-GrossProfit/GrossLoss, 4)
        backreport['平均損益'] = round(Profit/Trades, 4)
        backreport['最大ドローダウン'] = round(MDD, 4)
        backreport['リカバリーファクター'] = round(Profit/MDD, 4)
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


if __name__ == "__main__":
    info = profit(0)
    os.mkdir(str(info.S_DIR))
    dir = r"C:\data\90_profit\05_input\FX_soruce"
    ETF=['USDJPY','AUDJPY','EURJPY','GBPJPY','AUDUSD','GBPUSD','EURUSD']
    save_name = os.path.join(info.S_DIR,"all_report_FX.csv")
    if os.path.exists(save_name):
        os.remove(save_name)
#時間指定ネタ
#    tsd = pd.read_csv( 'USDJPY_15.csv',index_col=0,parse_dates=True)
#    td=tsd[tsd.index.hour==8]


    for code in ETF:
#        try:
        print(code)
#        tsd = info.csv_connect(dir + "//" + code ,code)#★★★★★★★
        para =  ['rng7','rng30','rng200','rng1000']
        para =[ i for i in range(24)]
        col = 0.1
#       CSVから読み込む場合
        tsd = pd.read_csv(os.path.join(info.INPUT_DIR ,code + '_15.csv'),index_col=0,parse_dates=True)#●●●●●●●●●●●
        if len(tsd) > 1:
    #       ５分間隔のデータ作成
#            tsd = info.priod_edit(tsd,'15T')#★★★★★★★
#            tsd.to_csv(os.path.join(info.INPUT_DIR ,code + '_15.csv') )#★★★★★★★

#                Trade, PL=info.breakout_simple_f(tsd,window0,window9,f0,f9,'rng200',i)
#                Equity,backreport = info.BacktestReport(Trade, PL)
#                info.save_to_csv(save_name,code+ str(i) + "_3breakout_simple_f",backreport)

#                all_ = pd.concat([tsd,Trade,PL],axis=1)
#                all_.to_csv(code + str(i) + '_dital.csv' )

#                print("end")
#                exit()

            print("1")
            for i in para:
                window=350
                multi=2.5
                PL = info.breakout_ma_std(tsd,window,multi,col,i)
                Equity,backreport = info.BacktestReport(PL)
                info.save_to_csv(save_name,code+ str(i)+"_1BacktestReport",backreport)
                PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_1BacktestReport_dital.csv'))

            print("2")
            for i in para:
                window0=20
                window9=10
                PL=info.breakout_simple(tsd,window0,window9,col,i)
                Equity,backreport = info.BacktestReport(PL)
                info.save_to_csv(save_name,code+ str(i) + "_2breakout_simple",backreport)
                PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_2breakout_simple_dital.csv'))

            print("3")
            for i in para:
                window0=20
                window9=10
                f0=25
                f9=350
                PL=info.breakout_simple_f(tsd,window0,window9,f0,f9,col,i)
                Equity,backreport = info.BacktestReport(PL)
                info.save_to_csv(save_name,code+ str(i) + "_3breakout_simple_f",backreport)
                PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_3breakout_simple_f_dital.csv'))

            print("4")
            for i in para:
                window0=100
                window9=350
                PL=info.breakout_ma_two(tsd,window0,window9,col,i)
                Equity,backreport = info.BacktestReport(PL)
                info.save_to_csv(save_name,code+ str(i)+"_4breakout_ma_two",backreport)
                PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_4breakout_ma_two.csv'))

            print("5")
            for i in para:
                window0=100
                window9=250
                window5=350
                PL=info.breakout_ma_three(tsd,window0,window9,window5,col,i)
                Equity,backreport = info.BacktestReport(PL)
                info.save_to_csv(save_name,code+ str(i)+"_5breakout_ma_three",backreport)
                PL.to_csv(os.path.join(info.S_DIR,code + str(i) + '_5breakout_ma_three.csv'))

    #            詳細調査の場合
    #            all_ = pd.concat([tsd,axis=1)
    #            all_.to_csv(code + 'dital.csv' )



#        except:
#            pass
    import shutil
    shutil.copy2(__file__, info.S_DIR)


#    print("end",__file__)