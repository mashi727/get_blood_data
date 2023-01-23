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
wait_for_page = 1.7
# ページ遷移を伴わない場合
wait_for_nopage = 0.7


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
    ''' .passwordファイルには
    BLOODCODE = 'xxxxxxxxxx'
    PASSWORD = 'xxxxxxxx'
    RECORDPASSWORD = 'xxxx'
    と記述する。
    '''
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
    #
    # ログイン後、献血記録確認のパスワードを入力すると
    # 「献血記録を確認」の初期画面として、最新のデータから3回分の血液などのデータが表示される。
    # このページには過去全ての献血日と種別が含まれ、表示してる3回分のデータのみ aria-hidden="false" となっている。
    # また、血液の分析結果の項目が2009.3.15以降変更となっている。
    # 
    # このツールでは2009.3.15以降のデータのみ取得することとする。
    # 2009.3.15以降の献血回数の取得
    date_of_kenketsu = driver.find_elements(By.CLASS_NAME, 'mod-past-data__date') # 献血回数（すべての献血日の数を取得）
    num_of_kenketsu_all = len(date_of_kenketsu)
    num_of_kenketsu = 0
    for i in range(len(date_of_kenketsu)):
        # 表示を3の倍数とするために作られたデータは''が入っておりValueErrorになるので、エラー処理を行なう。
        try:
            # .textだとaria-hidden="true"の値が''で取得されるので、get_attribute("textContent")を使用する必要がある。
            kenketsubi = dt.strptime(date_of_kenketsu[i].get_attribute("textContent"), '%Y/%m/%d').date()
            change_date = date(2009, 3, 14) # 血液の検査結果が変更になった2009.3.15以降を前日より大きいと表現した。
            if (kenketsubi > change_date) == True:
                num_of_kenketsu = num_of_kenketsu + 1
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
        num_of_kenketsu_all (int): 過去に献血した回数、最新のデータがリストの最も後ろになっているため、forループの開始用に使用する。

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
    # 19種類のデータ分ループして値を取り込む
    kenketsu_raw_data = driver.find_elements(By.CLASS_NAME, 'mod-result-table__data')
    for i in range(len(kenketsu_raw_data)):
        kenketsu_data.append(kenketsu_raw_data[i].text.split()) # [a b c]となっているので、splitが必要
        # 各種別のデータが3つずつの組になっているので、献血日ごとのデータに並び替える
        new_list = list(flatten(kenketsu_data))[2::3] + list(flatten(kenketsu_data))[1::3] +list(flatten(kenketsu_data))[0::3]
    kenketsu_data_reshape = np.array(new_list).reshape(3,19).tolist()
    return kenketsu_data_reshape, index


def main():
    num_of_kenketsu, num_of_kenketsu_all = login_and_get_param()
    # 血液データの種別を格納するリストをもとにdataframeを作成
    cols = ['献血種別','血圧（最高）','血圧（最低）','脈拍','ALT（GPT）','γ-GTP','総蛋白TP','アルブミンALB','ALB/G','CHOL','GALB','RBC','Hb','Ht','MCV','MCH','MCHC','WBC','PLT']
    df = pd.DataFrame(columns=cols)
    turn_num = math.ceil(num_of_kenketsu/3)
    for times in range(1,turn_num+1,1):
        kenketsu_data_reshape, index = get_data(times, num_of_kenketsu_all)
        # dfへデータを格納
        df = pd.concat([df,pd.DataFrame(data=kenketsu_data_reshape, index=index, columns=cols)])
        # チェック用にdfを表示する。
        # print(tabulate(df, df.columns,tablefmt='github', showindex=True))
        time.sleep(wait_for_page)
        # データを取得してページを進めており、最後のデータを取得した後にページを進める必要はないためにif文を入れている。
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
    date = dt(2009, 3, 14)
    # 2009/3/15以降の献血回数が3で割り切れないとき、古いデータが最大2行紛れ込む可能性があるため以下の処理を追加する。
    df = df[df.index > date]
    print(tabulate(df, df.columns,tablefmt='github', showindex=True))
    df.to_csv('./blood_data.csv')
    time.sleep(wait_for_page)
    driver.quit()

if __name__ == "__main__":
    main()
