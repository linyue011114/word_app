from bs4 import BeautifulSoup
import csv
import re

# 1. leap1800.htmlを読み込み
with open('leap1800.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

# 2. CSVファイルを開く（上書きモード）
with open('leap1800.csv', 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)

    # 3. <tr>タグをすべて取得
    rows = soup.find_all('tr')

    for tr in rows:
        # 4. <td class="column-1">, column-2, column-3を取得
        col1 = tr.find('td', class_='column-1')
        col2 = tr.find('td', class_='column-2')
        col3 = tr.find('td', class_='column-3')

        if col1 and col2 and col3:
            number = col1.text.strip()        # 番号
            word = col2.text.strip()          # 英単語
            meaning_full = col3.text.strip()  # 意味（例: [自] ①賛成する ②（主語の中で）意見が一致する ...）

            # 5. 品詞（[自]や[他]など）を除去
            meaning_no_pos = re.sub(r'^\[.*?\]\s*', '', meaning_full)

            # 6. 最初の「①〜」だけ抽出。番号のあと意味だけ。
            match = re.search(r'①([^②③④⑤⑥⑦⑧⑨⑩]*)', meaning_no_pos)
            if match:
                meaning_first = match.group(1).strip()
            else:
                # ①がない場合は意味全文の最初の部分だけを取る（例として50文字まで）
                meaning_first = meaning_no_pos[:50].strip()

            # 7. CSVに書き込み（番号、英単語、意味①だけ）
            writer.writerow([number, word, meaning_first])

print('変換が完了しました。leap1800.csv を確認してください。')
