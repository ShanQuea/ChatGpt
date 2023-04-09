import os
import sqlite3

from flask import Flask, render_template, request, jsonify, session
import openai


app = Flask(__name__)
app.secret_key = os.urandom(16) # 设置 Flask 的 session 密钥

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

# 注册路由
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    # 在这里可以添加验证用户名和密码的逻辑，例如检查用户名是否已存在等
    # 如果验证成功，将用户名保存到 session 中，并将账号信息存入数据库
    session["username"] = username
    register_account(username, password)
    return jsonify({"result": "success", "username": username})

# 登录路由
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    # 在这里可以添加验证用户名和密码的逻辑，例如从数据库中查询用户信息
    # 如果验证成功，将用户名保存到 session 中
    session["username"] = username
    return jsonify({"result": "success", "username": username})

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