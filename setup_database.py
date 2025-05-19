import sqlite3
import csv

# DB作成
conn = sqlite3.connect('words.db')
c = conn.cursor()

# テーブル作成
c.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        meaning TEXT NOT NULL,
        difficulty INTEGER,
        category TEXT
    )
''')

# データ挿入（CSVから）
with open('leap1800.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # ヘッダーをスキップ
    for row in reader:
        word, meaning, difficulty, category = row
        c.execute('''
            INSERT INTO words (word, meaning, difficulty, category)
            VALUES (?, ?, ?, ?)
        ''', (word, meaning, int(difficulty), category))

conn.commit()
conn.close()
