import sqlite3
import csv

conn = sqlite3.connect('words.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS words')
cursor.execute('CREATE TABLE words (word TEXT, meaning TEXT)')

with open('leap1800.csv', 'r', encoding='UTF-8') as file:
    reader = csv.reader(file)
    next(reader)  # ヘッダーをスキップする場合
    for row in reader:
        english = row[0].strip()
        japanese = row[1].strip()
        cursor.execute("INSERT INTO words (word, meaning) VALUES (?, ?)", (english, japanese))
conn.commit()
conn.close()
print("登録完了")
