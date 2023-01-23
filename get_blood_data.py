import time
import collections
import numpy as np
import pandas as pd
from tabulate import tabulate
from datetime import datetime as dt
from datetime import date
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
wait_for_page = 2
# ページ遷移を伴わない場合
wait_for_nopage = 0.7


def login_and_get_param():
    """_summary_
    
    この関数では、
    1. 献血データの確認のためのログイン処理
    2. 献血回数の抽出と、2009.3.15以前までの最も古い献血データのを含む結果の表示画面への遷移
    3. ページをめくる回数を戻す
    ということを行います。
    
    Returns:
        int : turn_num
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
    #
    # 「献血記録を確認」の初期画面では、最新のデータから3回分の血液などのデータが表示され、
    # 「過去の献血履歴」ページでは10回分の献血日と献血種別などの一覧（血液などのデータなし）が表示される。
    # 
    # データの取得は、のちのちindexによりソートしなくてよくするため 古いデータから行なうこととする。
    #
    # ということで、やることは以下のとおり。
    # １．最も古いデータを表示するために、ページをめくる回数を取得する。
    #     ページをめくる回数は、いま表示している「献血記録を確認」ページに含まれる（※）献血日のデータ数（mod-past-data__date）から算出する。
    #     この際、献血日のデータ数が実際に献血した回数ではなく、3の倍数になる仕様となっている（献血のデータが常に3回分表示されるため）ことに注意する必要がある。
    #     （なお、3の倍数に調整された場合には、日付のデータに''（空のデータ）が、血圧等の結果データに '-' が入っている。）
    #     （※）過去の献血履歴のページでは表示されないので、このページで取得する必要があることに注意する必要がある。
    kenketsu_date_raw = driver.find_elements(By.CLASS_NAME, 'mod-past-data__date') # 献血回数（献血日の数を取得）
    # range(start, stop, step)
    kenketsu_num_after_change = 0
    for i in range(len(kenketsu_date_raw)):
        # 表示を3の倍数とするために作られたデータは''が入っておりValueErrorになるので、エラー処理を行なう。
        try:
            # .textだとaria-hidden="true"の値が''で取得されるので、get_attribute("textContent")を使用する必要がある。
            kenketsubi = dt.strptime(kenketsu_date_raw[i].get_attribute("textContent"), '%Y/%m/%d').date()
            change_date = date(2009, 3, 14) # 2009.3.15以降、血液の検査結果が変更になった
            if (kenketsubi > change_date) == True:
                kenketsu_num_after_change = kenketsu_num_after_change + 1
            else:
                pass 
        except ValueError as e:
            pass
    print(kenketsu_num_after_change)
    #     各ページごと10回分表示されるので、献血日のデータ数に対して、10による商をもとめて、めくる回数を決定している。
    # ２．過去の献血履歴（10回分の一覧表示）のページに遷移して、１で求めた回数分ページをめくり最も古い血液などのデータを表示するページ（3回分）に遷移する。
    driver.find_element(By.LINK_TEXT, '過去の献血履歴はこちら').click() # 過去の献血履歴（10回分の献血日と献血種別などが表示される）のページに遷移する。
    time.sleep(wait_for_page)
    # ３．ページをめくる回数(n)が決まり過去の献血履歴の画面が表示できたので、もっとも古い献血日を含む一覧画面に遷移する。
    n = len(kenketsu_date_raw) // 10 # 私の場合2023.1の時点で8（81回分のデータが、3の倍数の81になるため 81//10 = 8）
    for i in range(n):
        driver.find_element(By.ID, 'RecordList:j_id41:RecordList:j_id50').click()
        time.sleep(wait_for_nopage)
    # ４．2009.3.15以降で、もっとも古い献血のデータの表示画面に遷移する。
    # j_id54:n(n=0-9)で、10個の献血データ表示ボタンにアクセスできる。
    # 献血データ変更後のもっとも古い献血データは、回数の
    x = (kenketsu_num_after_change % 10) - 1 
    button_strings = 'RecordList:j_id41:RecordList:j_id54:'+str(f"{x}")+':inspectionResult'
    driver.find_element(By.ID, button_strings).click()
    time.sleep(wait_for_page)

    # 日付と献血種別は、表示している献血回数分しか取得できないため、取得の際には、表示している献血回数を指定する必要がある。
    # 血液などのデータ表示（3回分）ページをめくる回数を計算する。
    turn_num = kenketsu_num_after_change//3 # 2023.1の時点で、81/3 = 17
    return turn_num


def get_data(times):
    # 表示されている血液の分析結果などを取得する（3回分）。
    # 取得したデータは、日付をインデックスとして献血種別（1）、血圧、脈拍（3）及び血液の分析結果（15）をデータとして格納（計19種のデータとなる）
    # インデックス用の献血日
    kenketsu_date = driver.find_elements(By.CLASS_NAME, 'mod-past-data__date') # 表示されている献血日の取得（表示されていない日を取得すると、空になる）
    # 献血種別
    kenketsu_kind = driver.find_elements(By.CLASS_NAME, 'mod-past-data__result') # 表示されている献血日の献血種別を取得（表示されていない日は、同じく空になる）

    # dataframeのインデックス用に日付を作成（3回分を取得するので実行されるたびに初期化する）
    index = [] # 献血日
    # 取得したデータのリストを作成する。（3回分を取得するので実行されるたびに初期化する）
    kenketsu_data = []
    # 回数のチェック用
    # print('回数',3*(times -1),3*times)
    # range(start, stop, step)
    for i in range(3*(times -1), 3*times, 1):
        index.append(kenketsu_date[i].text)
        kenketsu_data.append(kenketsu_kind[i].text)
    #print(index)
    # 19種類のデータ分ループして値を取り込む
    kenketsu_raw_data = driver.find_elements(By.CLASS_NAME, 'mod-result-table__data')
    for i in range(len(kenketsu_raw_data)):
        kenketsu_data.append(kenketsu_raw_data[i].text.split()) # [a b c]となっているので、splitが必要
        # 各種別のデータが3つずつの組になっているので、献血日ごとのデータに並び替える
        new_list = list(flatten(kenketsu_data))[0::3] + list(flatten(kenketsu_data))[1::3] +list(flatten(kenketsu_data))[2::3]
    kenketsu_data_reshape = np.array(new_list).reshape(3,19).tolist()
    return kenketsu_data_reshape, index


def main():
    turn_num = login_and_get_param()
    '''
    # 血液データの種別を格納するリストをもとにdataframeを作成
    cols = ['献血種別','血圧（最高）','血圧（最低）','脈拍','ALT（GPT）','γ-GTP','総蛋白TP','アルブミンALB','ALB/G','CHOL','GALB','RBC','Hb','Ht','MCV','MCH','MCHC','WBC','PLT']
    df = pd.DataFrame(columns=cols)
    for times in range(1,turn_num+1,1):
        kenketsu_data_reshape, index = get_data(times)
        # dfへデータを格納
        df = pd.concat([df,pd.DataFrame(data=kenketsu_data_reshape, index=index, columns=cols)])
        # チェック用にdfを表示する。
        # print(tabulate(df, df.columns,tablefmt='github', showindex=True))
        time.sleep(wait_for_page)
        # 献血データが重複しないよう、3つずつすすめる
        for i in range(3):
            driver.find_element(By.CSS_SELECTOR, '.is-next').click()
            time.sleep(wait_for_nopage)
        # すすめた期間の献血データを表示する(ボタンをクリック)
        driver.find_element(By.ID, 'RecordInspectionResult:j_id48:j_id49').click()
        time.sleep(wait_for_nopage) # ページの遷移を待って、次の処理へ
    
    print(tabulate(df, df.columns,tablefmt='github', showindex=True))
    '''
    time.sleep(wait_for_page)
    driver.quit()



if __name__ == "__main__":
    main()
