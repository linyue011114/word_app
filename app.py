from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import json
import csv
import unicodedata
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セッションを使う場合に必須
import re

# clean_meaning関数を以下のように変更（複数意味の取得用）
def clean_meaning(raw):
    import re
    # []や（）、＜＞、〈〉を除去
    cleaned = re.sub(r'\[.*?\]', '', raw)
    cleaned = re.sub(r'（.*?）', '', cleaned)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'＜.*?＞', '', cleaned)
    cleaned = re.sub(r'〈.*?〉', '', cleaned)

    # 全角カンマ「，」、半角カンマ「,」、句点などで分割
    # r'[，,、．.。]\s*' として区切り文字に全角カンマを入れているか確認してください
    meanings = re.split(r'[，,、．.。]\s*', cleaned)
    # 空文字削除、stripで前後空白除去
    meanings = [m.strip() for m in meanings if m.strip()]
    # 空文字を除去し、前後の空白を削除
    cleaned_meanings = [m.strip() for m in meanings if m.strip() != '']
    return cleaned_meanings
def normalize_text(text):
    return unicodedata.normalize('NFKC', text)
def preprocess_text(text):
    text = unicodedata.normalize('NFKC', text)  # 正規化
    text = text.replace('～', '~')  # すべての「～」を統一
    text = text.replace('〜', '~')  # 波ダッシュ→半角チルダ
    text = text.replace('ー', '~')  # 長音符→半角チルダ
    return text.strip().lower()  # 前後の空白を除去＆小文字変換
def unify_spaces(text):
    text = text.replace('\u3000', ' ')
    return text.strip()  # 前後の不要な空白を削除
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # フォームからの情報を取得
        mode = request.form['mode']  # 形式名（例 test_e2j など）
        start = int(request.form['start'])
        end = int(request.form['end'])
        count = int(request.form['count'])
        random_flag = request.form['random']

        # GETパラメータにして該当形式のページへリダイレクト
        return redirect(url_for(mode, start=start, end=end, count=count, random=random_flag))
    
    # GETは設定画面の表示
    return render_template('settings.html')

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/quiz_j2e', methods=['GET', 'POST'])
def quiz_j2e():
    if request.method == 'POST':
        user_answer = request.form['answer'].strip().lower()
        correct_answer = request.form['correct_answer'].strip().lower()
        meaning = request.form['meaning']
        is_correct = (user_answer == correct_answer)

        # 現在の問題番号を進める
        session['current_index'] = session.get('current_index', 0) + 1
        idx = session['current_index']
        quiz_data = session.get('quiz_data', [])

        if idx < len(quiz_data):
            next_q = quiz_data[idx]
            return render_template('quiz_j2e.html',
                                   show_result=True,
                                   meaning=meaning,
                                   correct_answer=correct_answer,
                                   user_answer=user_answer,
                                   is_correct=is_correct,
                                   has_next=True,
                                   next_meaning=next_q['meaning'],
                                   next_correct_answer=next_q['word'])
        else:
            # 最後の問題
            return render_template('quiz_j2e.html',
                                   show_result=True,
                                   meaning=meaning,
                                   correct_answer=correct_answer,
                                   user_answer=user_answer,
                                   is_correct=is_correct,
                                   has_next=False)

    else:
        # GET: クイズ開始時
        start = int(request.args.get('start', 1))
        end = int(request.args.get('end', 100))
        count = int(request.args.get('count', 10))
        random_flag = request.args.get('random', 'yes')

        conn = sqlite3.connect('words.db')
        cursor = conn.cursor()

        if random_flag == 'yes':
            cursor.execute("""
                SELECT word, meaning FROM words
                WHERE number BETWEEN ? AND ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (start, end, count))
        else:
            cursor.execute("""
                SELECT word, meaning FROM words
                WHERE number BETWEEN ? AND ?
                LIMIT ?
            """, (start, end, count))

        rows = cursor.fetchall()
        conn.close()

        quiz_data = [{'word': row[0], 'meaning': row[1]} for row in rows]

        session['quiz_data'] = quiz_data
        session['current_index'] = 0

        if quiz_data:
            first_q = quiz_data[0]
            return render_template('quiz_j2e.html',
                                   meaning=first_q['meaning'],
                                   correct_answer=first_q['word'],
                                   show_result=False)
        else:
            return "該当する問題がありません。"
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        word = request.form['word']
        correct_answer_raw = request.form['correct_answer']
        # 1. ユーザー入力を1回だけ取得して正規化
        raw_answer = request.form.get('answer', '')
        user_answer = unify_spaces(preprocess_text(raw_answer))

        # 2. 正解データも1回のリスト内包表記で正規化
        clean_answers = clean_meaning(correct_answer_raw)
        correct_answers = [unify_spaces(preprocess_text(m)) for m in clean_answers]
        is_correct = user_answer in correct_answers
        # 次の出題の準備
        session['current_index'] += 1
        next_index = session['current_index']

        if next_index < len(session['quiz_data']):
            next_q = session['quiz_data'][next_index]
            return render_template('quiz.html',
                                   show_result=True,
                                   word=word,
                                   correct_answer=correct_answer_raw,
                                   user_answer=user_answer,
                                   is_correct=is_correct,
                                   next_word=next_q['word'],
                                   next_correct_answer=next_q['meaning'],
                                   has_next=True)
        else:
            return render_template('quiz.html',
                                   show_result=True,
                                   word=word,
                                   correct_answer=correct_answer_raw,
                                   user_answer=user_answer,
                                   is_correct=is_correct,
                                   has_next=False)

    # GET: クイズ開始時
    start = int(request.args.get('start', 1))
    end = int(request.args.get('end', 1800))
    count = int(request.args.get('count', 10))
    random_flag = request.args.get('random', 'yes')
    # セッションに保存（初回アクセス時のみでOK）
    session['start'] = start
    session['end'] = end
    session['count'] = count
    session['random'] = random_flag

    with open('leap1800.csv', newline='', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        rows = reader[start - 1:end]

    if random_flag == 'yes':
        selected_rows = random.sample(rows, min(count, len(rows)))
    else:
        selected_rows = rows[:count]

    quiz_data = [{'word': row[1], 'meaning': row[2]} for row in selected_rows]

    # セッションに保存
    session['quiz_data'] = quiz_data
    session['current_index'] = 0

    first_q = quiz_data[0]
    return render_template('quiz.html',
                           show_result=False,
                           word=first_q['word'],
                           correct_answer=first_q['meaning'])
# テスト形式（英語→日本語）のルート
@app.route('/test_e2j', methods=['GET', 'POST'])
def test_e2j():
    import json
    import csv
    import random

    if request.method == 'POST':
        questions = json.loads(request.form['questions'])

        score = 0
        results = []

        for i, q in enumerate(questions):
            user_answer = unify_spaces(preprocess_text(request.form.get(f'answer_{i}', '')))
            correct_answer = [unify_spaces(preprocess_text(meaning)) for meaning in q['clean_meaning']]
            print(f"User Answer: {repr(user_answer)}")
            print(f"Correct Answer: {repr(correct_answer)}")
            is_correct = user_answer in correct_answer
            if is_correct:
                score += 1
            results.append({
        'word': q['word'],
        'correct_answer': ', '.join(q['clean_meaning']),  # 複数意味を表示用に結合
        'user_answer': user_answer,
        'is_correct': is_correct
            })
        return render_template('test_result.html', results=results, score=score, total=len(questions))

    # GET（出題）の処理
    start = int(request.args.get('start', 1))
    end = int(request.args.get('end', 100))
    count = int(request.args.get('count', 10))
    random_flag = request.args.get('random', 'no')

    with open('leap1800.csv', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)[start-1:end]

    if random_flag == 'yes':
        selected_rows = random.sample(rows, min(count, len(rows)))
    else:
        selected_rows = rows[:count]

    questions = [{'word': row[1], 'meaning': row[2], 'clean_meaning': clean_meaning(row[2])} for row in selected_rows]
    print(questions)
    questions_json = json.dumps(questions)

    return render_template('test_e2j.html', questions=questions, questions_json=questions_json)

# テスト形式（日→英）のルート
@app.route('/test_j2e', methods=['GET', 'POST'])
def test_j2e():
    if request.method == 'POST':
        # POSTされたフォームから問題数を取得
        question_count = int(request.form['question_count'])

        score = 0  # 正解数をカウント
        results = []  # 各問題の採点結果を格納

        for i in range(question_count):
            # ユーザーの回答を取得（小文字にして比較しやすく）
            user_answer = request.form.get(f'answer{i}', '').strip().lower()
            # 正しい英単語
            correct_answer = request.form.get(f'correct{i}', '').strip().lower()
            # 日本語の意味（結果表示用）
            meaning = request.form.get(f'meaning{i}', '')

            # 正誤判定
            is_correct = (user_answer == correct_answer)
            if is_correct:
                score += 1

            # 各問題の結果を保存
            results.append({
                'meaning': meaning,
                'correct_answer': correct_answer,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        # 採点結果を表示するテンプレートに渡す
        return render_template('test_result_j2e.html', results=results, score=score, total=question_count)
    
    else:
        # GETパラメータを取得。デフォルト値を指定しておく
        start = int(request.args.get('start', 1))
        end = int(request.args.get('end', 100))
        count = int(request.args.get('count', 10))
        random_flag = request.args.get('random', 'yes')

        # 初回表示時：ランダムに10問出題
        conn = sqlite3.connect('words.db')
        cursor = conn.cursor()
        cursor.execute("SELECT word, meaning FROM words WHERE number BETWEEN ? AND ?", (start, end))
        rows = cursor.fetchall()
        conn.close()

        if random_flag == 'yes':
            selected_rows = random.sample(rows, min(count, len(rows)))
        else:
            selected_rows = rows[:count]

        # 表示用に辞書に変換
        questions = [{'word': row[0], 'meaning': row[1]} for row in selected_rows]

        # 問題ページを表示
        return render_template('test_j2e.html', questions=questions)
# ←←← 最後にこれ！
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)