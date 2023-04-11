import sqlite3
import random
import string
import PySimpleGUI as sg


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


layout = [
    [sg.Text('生成卡密数量:', size=(15, 1)), sg.InputText('', key='-NUM-')],
    [sg.Text('卡密对应的count值:', size=(15, 1)), sg.InputText('', key='-COUNT-')],
    [sg.Button('生成卡密'), sg.Button('退出')],
    [sg.Output(size=(50, 10), key='-OUTPUT-')]
]


window = sg.Window('卡密生成工具', layout)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == '退出':
        break

    if event == '生成卡密':
        try:
            num_of_cards = int(values['-NUM-'])
            count_value = int(values['-COUNT-'])

            # 清空输出框内容
            window['-OUTPUT-'].update('')

            for i in range(num_of_cards):
                card_key = generate_card_key(16)
                write_to_card_txt(card_key)
                write_to_card_db(card_key, count_value)
                print(f'生成卡密: {card_key}，count值: {count_value}')
            print('卡密生成并写入成功！')
        except ValueError:
            print('请输入有效的数字！')

window.close()
