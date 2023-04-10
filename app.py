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
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"User: {user_message}\nBot:",
        max_tokens=100
    )
    bot_message = response["choices"][0]["text"].strip()
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
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# 注册新账号
def register_account(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, password))
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
    user_message = request.form["user_message"]
    bot_message = chat_with_gpt(user_message)
    return jsonify({"message": bot_message})


if __name__ == "__main__":
    create_accounts_table()  # 创建账号表格
    app.run(debug=True)
