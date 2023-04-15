import os
import time
import sqlite3
import openai
import json
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.urandom(16)  # 设置 Flask 的 session 密钥

# 配置 OpenAI API 密钥
openai.api_key = "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"


def clear_user_chat_history(username):
    user_chat_history_folder = os.path.join("chat", username)
    chat_history_file = os.path.join(user_chat_history_folder, "chat_history.json")

    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'w') as f:
            f.write('[]')


def get_user_chat_history(username):
    user_chat_history_folder = os.path.join("chat", username)
    chat_history_file = os.path.join(user_chat_history_folder, "chat_history.json")

    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'r') as f:
            chat_history_str = f.read()
            if chat_history_str:
                # 将读取到的字符串解析为 JSON 格式
                chat_history = json.loads(chat_history_str)
                return chat_history
    return None


def add_user_chat_history(username, user_message, bot_message):
    user_chat_history_folder = os.path.join("chat", username)
    chat_history_file = os.path.join(user_chat_history_folder, "chat_history.json")

    if not os.path.exists(user_chat_history_folder):
        os.makedirs(user_chat_history_folder)
    chat_data = []
    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'r') as f:
            chat_data = json.load(f)
    chat_data.append({"role": "user", "content": user_message})
    chat_data.append({"role": "assistant", "content": bot_message})
    with open(chat_history_file, 'w') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=4)


def chat_with_gpt(user_message, username):
    if user_message.strip() == "/clear":
        # 清除用户聊天历史数据
        clear_user_chat_history(username)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))

        cursor.execute("UPDATE accounts SET chat_count = ? WHERE username = ?", (0, username))
        return "聊天历史已清除"

    start_time = time.time()
    chat_history = get_user_chat_history(username) or []
    chat_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        messages=chat_history,
        model="gpt-3.5-turbo-0301",
        max_tokens=2048,
        temperature=0.7,
        n=1
    )
    print(chat_history)
    # 将助手的回复添加到对话历史中
    bot_message = response["choices"][0]["message"]["content"].strip()
    add_user_chat_history(username, user_message, bot_message)

    end_time = time.time()
    time_taken = end_time - start_time
    print(f"执行时间：{time_taken} 秒")

    return bot_message


# 连接到 SQLite3 数据库
# 连接数据库
def connect_db():
    conn = sqlite3.connect("accounts.db")
    return conn


# 创建账号表格
def create_accounts_table(cursor):
    # 创建 accounts 表格
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                count INTEGER NOT NULL,
                chat_count INTEGER NOT NULL 
            )
        """)


# 注册新账号
def register_account(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    create_accounts_table(cursor)
    cursor.execute("INSERT INTO accounts (username, password, count, chat_count) VALUES (?, ?, ?, ?)",
                   (username, password, 5, 0))
    conn.commit()
    conn.close()


# 首页路由
@app.route("/")
def index():
    # 检查用户是否已登录，若未登录则跳转到登录页
    if "username" not in session:
        return render_template("login.html")
    return render_template("index.html", username=session["username"])


# 登录路由
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # 连接到数据库
    conn = connect_db()
    cursor = conn.cursor()
    create_accounts_table(cursor)

    # 查询数据库中的账号信息
    cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
    account = cursor.fetchone()

    # 检查账号是否存在并验证密码
    if account is not None and account[2] == password:

        session["username"] = username
        session["conversation_history"] = []

        # 创建用户专属的聊天记录文件夹
        user_chat_history_folder = os.path.join("chat", username)
        if not os.path.exists(user_chat_history_folder):
            os.makedirs(user_chat_history_folder)

        # 检查用户聊天记录文件是否存在，如果没有则创建
        chat_history_file = os.path.join(user_chat_history_folder, "chat_history.json")
        if not os.path.exists(chat_history_file):
            with open(chat_history_file, "w") as f:
                json.dump([], f)

        return jsonify({"result": "success", "username": username})
    else:
        # 返回登录失败的 JSON 响应，包含错误信息
        return jsonify({"result": "fail", "error": "密码错误或账号不存在"})


# 注册路由
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        # 在这里可以添加验证用户名和密码的逻辑，例如检查用户名是否已存在等
        conn = connect_db()
        cursor = conn.cursor()
        create_accounts_table(cursor)

        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
        existing_account = cursor.fetchone()
        if existing_account is not None:
            conn.close()
            return jsonify({"result": "fail"})
        # 将账号信息插入到数据库
        if password != confirm_password:
            conn.close()
            return jsonify({"result": "error"})

        register_account(username, password)
        # 返回注册成功的 JSON 响应
        return jsonify({"result": "success", "username": username})
    else:
        # 如果是 GET 方法请求，则渲染注册页面
        return render_template("register.html")


# 登出路由
@app.route("/logout")
def logout():
    # 清空 session 中的用户名
    session.pop("username", None)
    return jsonify({"result": "success"})


# ChatGPT 聊天接口路由
@app.route("/chat", methods=["POST"])
def chat():
    # 获取用户信息
    user_message = request.form["user_message"]
    username = session["username"]

    # 查询数据库中的账号信息
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
    account = cursor.fetchone()

    times = account[3]
    chat_count = account[4]
    if times > 0:
        chat_count += 1
        #  修改聊天上限次数
        if chat_count == 10:
            chat_count = 0
            clear_user_chat_history(username)
            bot_message = "该对话 已经达到上限 已帮您清除聊天记录 开启新的对话"
        else:
            bot_message = chat_with_gpt(user_message, username)

        # 更新剩余次数 聊天次数
        cursor.execute("UPDATE accounts SET count = ? WHERE username = ?", (times - 1, username))
        cursor.execute("UPDATE accounts SET chat_count = ? WHERE username = ?", (chat_count, username))
        conn.commit()

        conn.close()
        return jsonify({"message": bot_message, "times": times - 1,"chat_count": chat_count})
    else:
        conn.close()
        return jsonify({"message": "次数不足 请及时充值", "times": times,"chat_count": chat_count})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
