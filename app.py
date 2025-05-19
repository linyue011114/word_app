from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import re
app = Flask(__name__)

def clean_meaning(raw):
    cleaned = re.sub(r'［.*?］', '', raw)
    cleaned = re.sub(r'（.*?）', '', cleaned)
    cleaned = re.split(r'[．。､,]', cleaned)[0]
    return cleaned.strip()

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
        return render_template('quiz_j2e.html', meaning=meaning, correct_answer=correct_answer,
                               user_answer=user_answer, is_correct=is_correct, show_result=True)
    else:
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

        if rows:
            word, meaning = rows[0]
        else:
            word, meaning = ("", "")

        return render_template('quiz_j2e.html', meaning=meaning, correct_answer=word, show_result=False)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        user_answer = request.form['answer'].strip().lower()
        correct_answer_raw = request.form['correct_answer'].strip().lower()
        # クリーン化して比較
        correct_answer = clean_meaning(correct_answer_raw).lower()
        is_correct = (user_answer == correct_answer)
        word = request.form['word']
        return render_template('quiz.html', word=word, correct_answer=correct_answer_raw,
                               user_answer=user_answer, is_correct=is_correct, show_result=True)
    else:
        start = int(request.args.get('start', 1))
        end = int(request.args.get('end', 100))
        count = int(request.args.get('count', 10))
        random_flag = request.args.get('random', 'yes')

        conn = sqlite3.connect('words.db')
        cursor = conn.cursor()

        if random_flag == 'yes':
            # 範囲内の単語からランダムに問題数分取得
            cursor.execute(f"""
                SELECT word, meaning FROM words
                WHERE number BETWEEN ? AND ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (start, end, count))
        else:
            # 範囲内の単語をID順に取得
            cursor.execute(f"""
                SELECT word, meaning FROM words
                WHERE number BETWEEN ? AND ?
                LIMIT ?
            """, (start, end, count))

        rows = cursor.fetchall()
        conn.close()

        # ここは1問だけ表示するならランダムに1問だけ渡すなど処理調整が必要
        # 例として最初の1問だけ取り出し
        if rows:
            word, meaning = rows[0]
        else:
            word, meaning = ("", "")

        return render_template('quiz.html', word=word, correct_answer=meaning, show_result=False)

# テスト形式（英語→日本語）のルート
@app.route('/test_e2j', methods=['GET', 'POST'])
def test_e2j():
    if request.method == 'POST':
        import json  # POSTのときに使うのでここでインポート

        # 隠しフィールドで送られてきた問題リストを復元
        questions = json.loads(request.form['questions'])  # ← ここも中にインデント！

        score = 0
        results = []

        for i, q in enumerate(questions):
            user_answer = request.form.get(f'answer_{i}', '').strip() #ユーザーが入力した情報を取＆文字列化→→user_answerに入れる
            is_correct = (user_answer == q['clean_meaning']) #クリーン済みのwords_dbと照らし合わせて正誤の結果をis_correctに保存する
            if is_correct: 
                score += 1 
            results.append({
                'word': q['word'],
                'correct_answer': q['clean_meaning'],
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        return render_template('test_result.html', results=results, score=score, total=len(questions)) 
        #test_result.htmlに結果を入れてそのtemplatesを表示させる
    else:
        # GETパラメータを取得。デフォルト値を指定しておく
        start = int(request.args.get('start', 1))
        end = int(request.args.get('end', 100))
        count = int(request.args.get('count', 10))
        random_flag = request.args.get('random', 'yes')

        # GETの処理（初回表示）
        conn = sqlite3.connect('words.db') # データベースに接続
        cursor = conn.cursor()
        cursor.execute("SELECT word, meaning FROM words WHERE number BETWEEN ? AND ?", (start, end))
        rows = cursor.fetchall()
        for row in rows:
            print(f"word: {row[0]}, meaning: {row[1]}")

        conn.close()

        if random_flag == 'yes':
            selected_rows = random.sample(rows, min(count, len(rows)))
        else:
            selected_rows = rows[:count]

        # selected_rows を使うように修正
        questions = [{'word': row[0], 'clean_meaning': clean_meaning(row[1])} for row in selected_rows]

        import json
        questions_json = json.dumps(questions)  # 明示的にJSONに変換

        # 両方をテンプレートに渡す
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
            questions = random.sample(rows, min(count, len(rows)))
        else:
            questions = rows[:count]

        # 表示用に辞書に変換
        questions = [{'word': row[0], 'meaning': row[1]} for row in rows]

        # 問題ページを表示
        return render_template('test_j2e.html', questions=questions)
# ←←← 最後にこれ！
if __name__ == '__main__':
    app.run(debug=True)