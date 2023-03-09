import sqlite3
import csv

dbpath = 'blood_data.db'
conn = sqlite3.connect(dbpath)
cursor = conn.cursor()

# テーブルを作成する
sql = "CREATE TABLE IF NOT EXISTS blood_data (\
        'donation_date' TEXT,\
        '献血種別' REAL,\
        '血圧（最高）' REAL,\
        '血圧（最低）' REAL,\
        '脈拍' REAL,\
        'ALT（GPT）' REAL,\
        'γ-GTP' REAL, \
        '総蛋白TP' REAL, \
        'アルブミンALB' REAL, \
        'ALB/G' REAL, \
        'CHOL' REAL, \
        'GALB' REAL, \
        'RBC' REAL, \
        'Hb' REAL, \
        'Ht' REAL, \
        'MCV' REAL, \
        'MCH' REAL, \
        'MCHC' REAL, \
        'WBC' REAL, \
        'PLT' REAL)"
cursor.execute(sql)

# CSVファイルからデータを読み込む
csvfile = open('blood_data.csv')
csv_reader = csv.reader(csvfile)
header = next(csv_reader)

# 読み込んだデータをSQLでテーブルに格納する
csv_rows = []
for row in csv_reader:
    row[2] = int(row[2])
    csv_rows.append(row)
cursor.executemany(
    "INSERT INTO blood_data (\
    'donation_date',\
    '献血種別',\
    '血圧（最高）' ,\
    '血圧（最低）' ,\
    '脈拍',\
    'ALT（GPT）',\
    'γ-GTP',\
    '総蛋白TP',\
    'アルブミンALB',\
    'ALB/G',\
    'CHOL',\
    'GALB',\
    'RBC',\
    'Hb',\
    'Ht',\
    'MCV',\
    'MCH',\
    'MCHC',\
    'WBC',\
    'PLT') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", csv_rows)


conn.commit()
csvfile.close()
conn.close()
