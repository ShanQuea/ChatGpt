import sqlite3
import PySimpleGUI as sg

def connect_db():
    conn = sqlite3.connect('../accounts.db')
    return conn

def get_accounts_data():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        return cursor.fetchall()

def update_count(account_id, new_count):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET count = ? WHERE id = ?", (new_count, account_id))
        conn.commit()

def display_accounts_table():
    accounts_data = get_accounts_data()
    layout = [
        [sg.Table(values=accounts_data,
                   headings=['ID', 'Username', 'Password', 'Count'],
                   display_row_numbers=False,
                   auto_size_columns=True,
                   select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                   enable_events=True,
                   key='-TABLE-')],
        [sg.Button('更新Count', key='-UPDATE-'), sg.Button('关闭')]
    ]
    window = sg.Window('次数设置', layout)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == '关闭':
            break

        if event == '-UPDATE-':
            selected_row = values['-TABLE-']
            if selected_row:
                account_id = accounts_data[selected_row[0]][0]
                new_count = sg.popup_get_text('输入新的数值:', default_text=str(accounts_data[selected_row[0]][3]))
                if new_count:
                    update_count(account_id, int(new_count))
                    sg.popup('次数更新成功.')
                    # 更新表格数据
                    accounts_data = get_accounts_data()
                    # 刷新窗口
                    window['-TABLE-'].update(values=accounts_data)

    window.close()

if __name__ == '__main__':
    display_accounts_table()
