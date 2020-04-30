#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings('ignore')  # 実行上問題ない注意は非表示にする

# Pandasのimport
import pandas as pd
import numpy as np
import sys, os
import common


#モデルの保存・読み込み
from sklearn.externals import joblib
#import sklearn
import joblib
import pickle
sys.path.append(common.LIB_DIR)

class scikit_learn:
    def __init__(self,num):
        self.num = num
        self.code = ""

    def RateOfChange(self, stock_data, haba, cnt=1):
        #変化率、正規化、標準化の3つに対応
        #パラメータ
        # stock_dataデータ
        # haba 2の場合おおよそ-1.0～1.0の範囲に収まるように調整
        # cnt 何日まえからの変化率 1は昨日からの変化率
        #全データの変化率 0～1
        if type(haba) == int:
            #文字列の列は削除する。
            for column in stock_data.columns:
                if stock_data[column].dtypes != 'int64' and stock_data[column].dtypes != 'float64':
                    stock_data.drop([column], axis=1, inplace=True)
#                    print("delete_column_" + column)
            stock_data = stock_data.pct_change(cnt) * haba
        else:
            class_type = haba
            if class_type == "MinMax":#正規化
                #前処理としてMinMaxScalerを用いる。まずはMinMaxScalerのインスタンスを作る。
                from sklearn.preprocessing import MinMaxScaler
                #パラメータcopyのTureは別オブジェクトとして
                MinMaxScaler(copy=True, feature_range=(0, 1))
                instance = MinMaxScaler() # インスタンスの作成
            elif  class_type == "Standard":#標準化
                from sklearn.preprocessing import StandardScaler
                #パラメータcopyのTureは別オブジェクトとして
                StandardScaler(copy=True, with_mean=True, with_std=True)
                instance = StandardScaler()  # インスタンスの作成

            for column in stock_data.columns:
                print(stock_data[column])
                x = stock_data[[column]].values
                try:
                    x_scaled = instance.fit_transform(x)
                    stock_data[column] = x_scaled
                except:
                    print("ERROR",stock_data[column].dtypes)
                    #labelsは数字、uniquesは文字列、全列を抽出
                    labels, uniques = pd.factorize(stock_data[column])
                    #新たにラベルを追加し、変換した整数を追加する。
                    stock_data[column] = labels

        stock_data = stock_data.replace([np.inf, -np.inf], np.nan)
        stock_data = stock_data.fillna(0)
        return stock_data

    def fx_data(self,df_info,hist_rang = 10):  #●サブデータ
        #nowを日付に置換(yyyy:mm:dd hh:mm:ss → yyyy-mm-dd)
#        df_info['now'] = df_info['now'].map(lambda x: x[:10].replace('/', '-'))
        #インデックス再設定 日時処理のみ
        df_info = df_info.set_index('now')
        #NaNを置換
        df_info = df_info.fillna(0)
        #数字以外は置換
        df_info = df_info.replace(['nan', '--', '-'], 0)
        list_w = []
        for col in df_info.columns:
            try:
                df_info[col] = df_info[col].map(lambda x: str(x).replace(',', ''))
                df_info[col] = df_info[col].astype(np.float64)
                #20200106追加
                ZERO = sum(df_info[col] == 0) / len(df_info)
                #全体で50%以上は削除
                if ZERO > 0.5:
                    print("del",col,ZERO)
                    list_w.append(col)
            except:
                print("NG",col)
                list_w.append(col)

        df_info = df_info.drop(list_w, axis=1)
        # 各列を変化率へ一括変換
        df_info = self.RateOfChange(df_info, 2, hist_rang)  # 第二引数 整数2の場合おおよそ-1.0～1.0の範囲 第三引数 何日まえからの変化率
        #df_info = self.RateOfChange(df_info,'MinMax',1) #正規化
        #df_info = self.RateOfChange(df_info,'Standard',1) #標準化

        return df_info

    def add_avg(self, df, code):  #●最後の引数は過去データ数
        #移動平均の計算、5日、25日、50日、75日
        #ついでにstdも計算する。（=ボリンジャーバンドと同等の情報を持ってる）
        #75日分のデータ確保
        nclose = len(df.columns)
        for i in range(1, 75):
            df[str(i)] = df[code].shift(+i)
        #移動平均の値とstdを計算する, skipnaの設定で一つでもNanがあるやつはNanを返すようにする
        df[code + 'MA5'] = df.iloc[:, np.arange(nclose, nclose+5)].mean(axis='columns', skipna=False)
        df[code + 'MA25'] = df.iloc[:, np.arange(nclose, nclose+25)].mean(axis='columns', skipna=False)
        df[code + 'MA50'] = df.iloc[:, np.arange(nclose, nclose+50)].mean(axis='columns', skipna=False)
        df[code + 'MA75'] = df.iloc[:, np.arange(nclose, nclose+75)].mean(axis='columns', skipna=False)

        df[code + 'STD5'] = df.iloc[:, np.arange(nclose, nclose+5)].std(axis='columns', skipna=False)
        df[code + 'STD25'] = df.iloc[:, np.arange(nclose, nclose+25)].std(axis='columns', skipna=False)
        df[code + 'STD50'] = df.iloc[:, np.arange(nclose, nclose+50)].std(axis='columns', skipna=False)
        df[code + 'STD75'] = df.iloc[:, np.arange(nclose, nclose+75)].std(axis='columns', skipna=False)
        #計算終わったら余分な列は削除
        for i in range(1, 75):
            del df[str(i)]
        #それぞれの平均線の前日からの変化（移動平均線が上向か、下向きかわかる）
        #shift(-1)でcloseを上に1つずらす
        df[code + 'diff_MA5'] = df[code + 'MA5'] - df[code + "MA5"].shift(1)
        df[code + 'diff_MA25'] = df[code + 'MA25'] - df[code + "MA25"].shift(1)
        df[code + 'diff_MA50'] = df[code + 'MA50'] - df[code + "MA50"].shift(1)
        df[code + 'diff_MA75'] = df[code + 'MA75'] - df[code + "MA75"].shift(1)
        #3日前までのopen, close, high, lowも素性に加えたい
        for i in range(1, 4):
            df['close-'+str(i)] = df[code].shift(+i)
#            df['open-'+str(i)] = df.open.shift(+i)
#            df['high-'+str(i)] = df.high.shift(+i)
#            df['low-'+str(i)] = df.low.shift(+i)
        #NaNを含む行を削除
        df = df.dropna()

        return df
    def model_save2(self,X_test,code):
        filename = os.path.join(common.MODEL,self.code.replace("/","") + '_finalized_model.sav')

        clf_2 = joblib.load(filename)
#        clf_2 = pickle.load(open(filename, 'rb'))
        pred_test_2 = clf_2.predict(X_test)
        return pred_test_2[-1]

    def main(self):
        code = 'USD/JPY'
        self.code = code
        df_info = common.select_sql(r'I07_fx.sqlite', 'select * from %(table)s where rowid > (select max(rowid) from %(table)s)  - %(key1)s' % {'table': 'gmofx', 'key1': 100})
        del df_info['MXN/JPY']
        del df_info['uptime']
        del df_info['result']
        for code in ['USD/JPY', 'EUR/USD', 'EUR/JPY', 'GBP/JPY']:
            try:
                del df_info[code.replace("/", "") + '_result']
            except:
                pass
        for code in ['USD/JPY','EUR/USD','EUR/JPY','GBP/JPY']:
            df_info = self.fx_data(df_info, 1)
            x_data = info.add_avg(df_info, code)
            result = self.model_save2(x_data,code)
            print("result",result)
            sqls = common.create_update_sql('I07_fx.sqlite', {code.replace("/","") + '_result':result}, 'gmofx')

    def main_bak(self):
        code = 'USD/JPY'
        self.code = code
        df_info = common.select_sql(r'I07_fx.sqlite', 'select * from %(table)s where rowid > (select max(rowid) from %(table)s)  - %(key1)s' % {'table': 'gmofx', 'key1': 100})
        del df_info['MXN/JPY']
        del df_info['uptime']
        del df_info['result']
        df_info = self.fx_data(df_info, 1)
        x_data = info.add_avg(df_info, code)
        print(len(x_data.columns))
        result = self.model_save2(x_data,code)
        print("result",result)
        sqls = common.create_update_sql('I07_fx.sqlite', {'result':result}, 'gmofx')

if __name__ == "__main__":
    info = scikit_learn(0)
    info.main_bak()
