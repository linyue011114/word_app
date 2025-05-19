import sqlite3
import csv

# DB接続
conn = sqlite3.connect('words.db')
cursor = conn.cursor()

# 既存のテーブルを削除
cursor.execute('DROP TABLE IF EXISTS words')

# ✅ number カラムを含めたテーブルを作成
cursor.execute('CREATE TABLE words (number INTEGER PRIMARY KEY, word TEXT, meaning TEXT)')

# CSVを開いて読み込む
with open('leap1800.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # ヘッダー行をスキップ

    for row in reader:
        number = int(row[0].strip())     # ✅ 1列目: number
        word = row[1].strip()            # ✅ 2列目: word
        meaning = row[2].strip()         # ✅ 3列目: meaning
        cursor.execute(
            "INSERT INTO words (number, word, meaning) VALUES (?, ?, ?)",
            (number, word, meaning)
        )

# 保存して終了
conn.commit()
conn.close()
print("✅ 正しく登録されました。")
