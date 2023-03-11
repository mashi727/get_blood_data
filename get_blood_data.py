'''
ラブラッドのサイトから、2009.3.15以降の献血データを取得するプログラムです。
実行には、本ファイルと同じ場所にログイン用のパスワードなどが記載された「.password」ファイルが必要です。
「.password」ファイルには、

BLOODCODE = 'xxxxxxxxxx'
PASSWORD = 'xxxxxxxx'
RECORDPASSWORD = 'xxxx'

と記述します。

実行すると、Chromeが立ち上がりログイン処理、血液の分析結果の取得などが行われ、スクリプトと同じフォルダに「blood_data.csv」が作成されます。

2009.3.15以降のデータを取得することとしたのは、血液の分析結果の項目が2009.3.15以降変更となっているためで
処理が面倒なので、このプログラムでは2009.3.15以降のデータのみ取得することとしました。

*** エラー関連 ***
実行すると、

selenium.common.exceptions.StaleElementReferenceException: Message: stale element reference: element is not attached to the page document

とエラーがでる場合があります。
ページの遷移が間に合っていないと思われますので、待ち時間をより長く設定してみてください。

本来は、状態変更をみるようにするのが良いのでしょうが、現状ではそこまでは行っていません。
そのうち、取得時間の節約やスキルアップのために、明示的な待機（WebDriverWait.until()）などを組み込むかもしれません。

ラブラッドサイトの解析は、Selenium IDEを使用しました。
これがなかったら、解析の時間がもっとかかっていたと思われます。

'''
import time
import collections
import numpy as np
import pandas as pd
from tabulate import tabulate
from datetime import datetime as dt
from datetime import date
import math

# dotenvに必要
import os
from dotenv import load_dotenv

def flatten(l):
    for el in l:
        if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary
from selenium.webdriver.common.by import By
driver = webdriver.Chrome()

# 待ち時間の設定
# ページ遷移を伴う場合
wait_for_page = 3
# ページ遷移を伴わない場合
wait_for_nopage = 2


def login_and_get_param():
    """
    この関数は
    
    1. 献血データの確認のためのログイン処理
    2. 2009.3.15以降の献血回数とすべての献血回数を返す
    
    ということを行います。
    
    Returns:
        int : num_of_kenketsu
        int : num_of_kenketsu_all
    """

    # ログイン用のパスワードなどを別ファイル(.password)から読み込み
    load_dotenv('.password')
    BLOODCODE = os.environ.get("BLOODCODE")
    PASSWORD = os.environ.get("PASSWORD")
    RECORDPASSWORD = os.environ.get("RECORDPASSWORD")

    # ログインページを開く
    driver.get('https://www.kenketsu.jp/RecordLogin?refURL=https%3A%2F%2Fwww.kenketsu.jp%2F')

    # 献血記録の確認までのログイン処理
    driver.find_element(By.NAME, "Login:j_id78:j_id80").send_keys(BLOODCODE)
    driver.find_element(By.NAME, "Login:j_id78:j_id82").send_keys(PASSWORD)
    driver.find_element(By.LINK_TEXT, 'ログイン').click()
    time.sleep(wait_for_page)
    driver.find_element(By.NAME, "RecordLogin:RecordLoginForm:kenketsuPassword").send_keys(RECORDPASSWORD)
    time.sleep(wait_for_nopage)
    driver.find_element(By.LINK_TEXT, '献血記録を確認する').click()
    time.sleep(wait_for_nopage)
    
    # ログイン後、献血記録確認のパスワードを入力すると
    # 「献血記録を確認」の初期画面として、最新のデータから3回分の血液などのデータが表示される。
    # このページには過去全ての献血日と種別が含まれ、表示してる3回分のデータのみ aria-hidden="false" となっている。
    # 2009.3.15以降の献血回数の取得
    date_of_kenketsu = driver.find_elements(By.CLASS_NAME, 'mod-past-data__date') # 献血回数（すべての献血日の数を取得）
    num_of_kenketsu_all = len(date_of_kenketsu)
    num_of_kenketsu = 0
    for i in range(len(date_of_kenketsu)):
        # 表示を3の倍数とするために作られたデータは''が入っておりValueErrorになるので、エラー処理を行なう。
        # 
        # 【2023.3.6追加】
        # うむ、今回は表示が3の倍数になっていない。。。
        # 今回は、By.CLASS_NAME, 'mod-past-data__date'が86になるよ。
        # 
        # #
        try:
            # .textだとaria-hidden="true"の値が''で取得されるので、get_attribute("textContent")を使用する必要がある。
            kenketsubi = dt.strptime(date_of_kenketsu[i].get_attribute("textContent"), '%Y/%m/%d').date()
            
            change_date = date(2009, 3, 14) # 血液の検査結果が変更になった2009.3.15以降を前日より大きいと表現した。
            if (kenketsubi > change_date) == True:
                # 2009.3.15以降（kenketsubi > change_date）であれば、カウントを増やす
                num_of_kenketsu = num_of_kenketsu + 1
                # print(num_of_kenketsu, kenketsubi)
            else:
                pass 
        except ValueError as e:
            pass
    return num_of_kenketsu, num_of_kenketsu_all # 私の場合、2023.1.23の時点で2009年の変更以降の献血回数は81回

def get_data(times, num_of_kenketsu_all):
    """
    表示されている3回分の血液の分析結果などを取得する。
    取得したデータは、日付をインデックスとして献血種別（1）、血圧、脈拍（3）及び血液の分析結果（15）をデータとして格納（計19種のデータとなる）
    
    Args:
        times (int): データを取得する回数
        num_of_kenketsu_all (int): 過去に献血した回数、最新のデータがリストの最も後ろになっているため、日付を取得するforループの開始用に使用する。

    Returns:
        kenketsu_data_reshape : 表示されている3回分データを整形してnumpyの配列として返す
        index : index用に、3回分の日付をリストとして返す
    """
    # インデックス用の献血日
    date_of_kenketsu = driver.find_elements(By.CLASS_NAME, 'mod-past-data__date') # 表示されている献血日の取得（表示されていない日を取得すると、空になる）
    # 献血種別
    kenketsu_kind = driver.find_elements(By.CLASS_NAME, 'mod-past-data__result') # 表示されている献血日の献血種別を取得（表示されていない日は、同じく空になる）

    # dataframeのインデックス用に日付を作成（3回分を取得するので実行されるたびに初期化する）
    index = [] # 献血日
    # 取得したデータのリストを作成する。（3回分を取得するので実行されるたびに初期化する）
    kenketsu_data = []
    for i in range(num_of_kenketsu_all+2-(times*3), num_of_kenketsu_all+2-((times+1)*3), -1):
        index.append(dt.strptime(date_of_kenketsu[i].text, '%Y/%m/%d')) # 日付の文字列をdatetimeに変換
        kenketsu_data.append(kenketsu_kind[i].text)
    # 18種類のデータ分ループして値を取り込む
    kenketsu_raw_data = driver.find_elements(By.CLASS_NAME, 'mod-result-table__data')
    for i in range(len(kenketsu_raw_data)):
        kenketsu_data.append(kenketsu_raw_data[i].text.split()) # [a b c]となっているので、splitが必要
        # 各種別のデータが3つずつの組になっているので、献血日ごとのデータに並び替える
        new_list = list(flatten(kenketsu_data))[2::3] + list(flatten(kenketsu_data))[1::3] +list(flatten(kenketsu_data))[0::3]
    try:
        if len(np.array(new_list)) == 57:
            kenketsu_data_reshape = np.array(new_list).reshape(3,19).tolist()
            return kenketsu_data_reshape, index
        else:
            # 献血記録の表示について、2009.3.14以前と以後が同時に表示される場合、検査項目が異なるため20項目のデータが表示され
            # 非該当のデータは - となるので、全データ数が60となり20個の3次元のデータにreshapeする。
            # 2009.3.14以前のデータの紛れ込み分は後ほど削除するので、ここでは5番目の「-」の列を削除する。
            #
            ### numpy.delete(arr, obj, axis=None)の使いかた ###
            # arr: 入力配列
            # obj: 削除する行番号や列番号を整数、スライス、リスト（配列）で指定
            # axis: 削除対象となる軸（次元）
            # #
            kenketsu_data_temp = np.array(new_list).reshape(3,20).tolist()
            kenketsu_data_reshape = np.delete(kenketsu_data_temp, 5, 1)
            return kenketsu_data_reshape, index
    except ValueError as e:
        pass

def main():
    # ログインして2009.3.15以降の献血回数とすべての献血回数を求める。
    num_of_kenketsu, num_of_kenketsu_all = login_and_get_param()
    # 血液データの種別を格納するリストをもとにdataframeを作成する。
    cols = ['献血種別','血圧（最高）','血圧（最低）','脈拍','ALT（GPT）','γ-GTP','総蛋白TP','アルブミンALB','ALB/G','CHOL','GALB','RBC','Hb','Ht','MCV','MCH','MCHC','WBC','PLT']
    df = pd.DataFrame(columns=cols) # データを作成する。
    # 2009.3.15以降の最も古い献血データを表示するまでデータをすすめる。
    # データは3つずつ進めているので、以下の処理とする。
    # この処理により、
    # 81回だと27回のめくりで、2009.3.15より前のデータは含まれない。
    # 2009.3.15より前のデータは、それぞれ、82回だと2回分、83回だと1回分、84回だと0回分含まれることとなる。
    turn_num = math.ceil(num_of_kenketsu/3) # 28
    '''
    if num_of_kenketsu % 3 == 0:
        turn_num = num_of_kenketsu // 3
    elif num_of_kenketsu % 3 == 1:
        turn_num = (num_of_kenketsu + 2) // 3
    elif num_of_kenketsu % 3 == 2:
        turn_num = (num_of_kenketsu + 1) // 3
    else:
        pass
    '''
    # 1からturn_numまでループ処理にて、データの取得 → データのめくり（重複しないよう3回分）を行なう。
    for times in range(1,turn_num+1,1):
        kenketsu_data_reshape, index = get_data(times, num_of_kenketsu_all)
        # dfへデータを格納
        df = pd.concat([df,pd.DataFrame(data=kenketsu_data_reshape, index=index, columns=cols)])
        # チェック用にdfを表示する。
        # print(tabulate(df, df.columns,tablefmt='github', showindex=True))
        time.sleep(wait_for_page)
        # データを取得してページを進めており、最後のデータを取得した後にページを進める必要はないため以下の処理を入れている。
        if times < turn_num:
            # 献血データが重複しないよう3つずつすすめる。
            for i in range(3):
                driver.find_element(By.CSS_SELECTOR, '.is-prev').click()
                time.sleep(wait_for_nopage)
            # すすめた期間の献血データを表示する(ボタンをクリック)
            driver.find_element(By.ID, 'RecordInspectionResult:j_id48:j_id49').click()
            time.sleep(wait_for_nopage) # ページの遷移を待って、次の処理へ
        else:
            pass
    '''
    *** 2009.3.15以前のデータの紛れ込みについて ***
    2009.3.15以降の献血回数が3で割り切れないとき、古いデータが最大2行紛れ込む可能性がある。
    したがって、ココで改めて2009.3.15以降のデータを抽出している。
    
    ラブラッドのサイトでは、2009.3.15以降と以前のデータを同時に表示する場合、データ数は19種類として表示され該当データがない箇所は'-'となる。データの取得は、最新のデータ表示にて取得したデータ種（18）のループとして回しているため途中でデータ数が19種になってもエラーなくデータが取得されるが、2009.3.15より前のデータは項目とその順番が異なるため、一部のデータがcolsで指定した列と異なるデータとなる。
    '''
    date = dt(2009, 3, 14)
    df = df[df.index > date]
    #print(tabulate(df, df.columns,tablefmt='github', showindex=True))
    df.sort_index(axis='index',ascending=True)
    df.to_csv('./blood_data.csv')
    driver.quit()

if __name__ == "__main__":
    main()
