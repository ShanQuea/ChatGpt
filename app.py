import os
import sqlite3
import openai

from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.urandom(16)  # 设置 Flask 的 session 密钥

# 配置 OpenAI API 密钥
openai.api_key = "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"


# ChatGPT 对话函数
def chat_with_gpt(user_message):
    # 之前的对话历史
    conversation_history = [
        {"role": "system", "content": "You: Hello, Bot: "},
        {"role": "user", "content": "How are you?"},  # 上一次用户消息
        {"role": "assistant", "content": "Bot: I'm doing well, thank you!"}  # 上一次助手的回复
    ]
    # 当前用户消息
    current_message = {"role": "user", "content": user_message}
    messages = conversation_history + [current_message]
    response = openai.ChatCompletion.create(
        messages=messages,
        model="gpt-3.5-turbo-0301",
        max_tokens=4000,
        temperature=0.7,
        n=1
    )
    conversation_history.append({"role": "user", "content": user_message})
    bot_message = response["choices"][0]["message"]["content"].strip()
    # 将助手的回复添加到对话历史中
    conversation_history.append({"role": "assistant", "content": bot_message})
    return bot_message

# 连接到 SQLite3 数据库
def connect_db():
    conn = sqlite3.connect("accounts.db")
    return conn

# 创建账号表格
def create_accounts_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# 注册新账号
def register_account(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (username, password, count) VALUES (?, ?, ?)",
                   (username, password, 5))  # 设置初始次数为5
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

    # 查询数据库中的账号信息
    cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
    account = cursor.fetchone()

    # 检查账号是否存在并验证密码
    if account is not None and account[2] == password:
        session["username"] = username
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
        # 在这里可以添加验证用户名和密码的逻辑，例如检查用户名是否已存在等

        # 将账号信息插入到数据库
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
    if times > 0:
        # 调用 ChatGPT 对话函数
        bot_message = chat_with_gpt(user_message)

        # 更新剩余次数
        cursor.execute("UPDATE accounts SET count = ? WHERE username = ?", (times - 1, username))
        conn.commit()
        conn.close()
        return jsonify({"message": bot_message, "times": times - 1})
    else:
        conn.close()
        return jsonify({"message": "次数不足 请及时充值", "times": times})


if __name__ == "__main__":
    create_accounts_table()  # 创建账号表格
    app.run(debug=True)
