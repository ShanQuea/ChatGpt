import sqlite3
import random
import string


conn = sqlite3.connect('card.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS card
             (id INTEGER PRIMARY KEY AUTOINCREMENT, card_no TEXT, count INTEGER)''')
conn.commit()
conn.close()

def generate_card_key(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
def write_to_card_txt(card_key):
    with open('card.txt', 'a') as f:
        f.write(card_key + '\n')

def write_to_card_db(card_key, count):
    conn = sqlite3.connect('card.db')
    c = conn.cursor()
    c.execute("INSERT INTO card (card_no, count) VALUES (?, ?)", (card_key, count))
    conn.commit()
    conn.close()


num_of_cards = int(input("生成的卡密数量: "))
count_value = int(input("生成的卡密对应的count值: "))

for i in range(num_of_cards):
    card_key = generate_card_key(16)
    write_to_card_txt(card_key)
    write_to_card_db(card_key, count_value)

print("卡密生成并写入成功！")
