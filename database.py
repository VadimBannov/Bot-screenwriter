import sqlite3
from config import *


# Функция для подключения к базе данных или создания новой, если её ещё нет
def create_db(database_name=DB_NAME):
    db_path = f'{database_name}'
    connection = sqlite3.connect(db_path)
    connection.close()


# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()


# Функция для выполнения любого sql-запроса для получения данных (возвращает значение)
def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows


# Функция для создания новой таблицы (если такой ещё нет)
# Получает название и список колонок в формате ИМЯ: ТИП
# Создаёт запрос CREATE TABLE IF NOT EXISTS имя_таблицы (колонка1 ТИП, колонка2 ТИП)
def create_table(table_name):
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name} ' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'role TEXT, ' \
                f'content TEXT, ' \
                f'date TEXT, ' \
                f'tokens INTEGER, ' \
                f'session_id INTEGER)'
    execute_query(sql_query)


# Функция для вывода всей таблицы (для проверки)
# Создаёт запрос SELECT * FROM имя_таблицы
def get_all_rows(table_name):
    quary = f"SELECT * FROM {table_name}"
    ram = execute_selection_query(quary)
    return ram


# Функиця для удаления всех записей из таблицы
# Создаёт запрос DELETE FROM имя_таблицы
def clean_table(table_name):
    execute_query(f"DELETE FROM {table_name}")


# Функция для вставки новой строки в таблицу
# Принимает список значений для каждой колонки и названия колонок
# Создаёт запрос INSERT INTO имя_таблицы (колонка1, колонка2) VALUES (?, ?)[значение1, значение2]
def insert_row(values):
    columns = "(user_id, role, content, date, tokens, session_id)"
    sq1_query = f"INSERT INTO {DB_TABLE_USERS_NAME} {columns} VALUES (?, ?, ?, ?, ?, ?)"
    execute_query(sq1_query, values)


# Функция для проверки, есть ли элемент в указанном столбце таблицы
# Создаёт запрос SELECT колонка FROM имя_таблицы WHERE колонка == значение LIMIT 1
def is_value_in_table(table_name, column_name, value):
    sq1_query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} = ?"
    raw = execute_selection_query(sq1_query, [value])
    return raw


def get_row_by_user_id(user_id):
    sql_query = f"SELECT * FROM {DB_TABLE_USERS_NAME} WHERE user_id = ?  ORDER BY date DESC LIMIT 1;"
    row = execute_selection_query(sql_query, [user_id])[0]
    return row


def get_user_session_id(user_id):
    sql_query = f"SELECT session_id FROM {DB_TABLE_USERS_NAME} WHERE user_id = ? ORDER BY date DESC LIMIT 1;"
    row = execute_selection_query(sql_query, [user_id])
    return row[0][0]


def get_dialogue_for_user(user_id, session_id):
    sql_query = (f'SELECT * FROM {DB_TABLE_USERS_NAME} WHERE user_id = ? AND tokens IS NOT NULL AND session_id = ? '
                 f'ORDER BY date ASC')
    row = execute_selection_query(sql_query, [user_id, session_id])
    return row


def get_size_of_session(user_id, session_id):
    sql_query = (f"SELECT tokens FROM {DB_TABLE_USERS_NAME} WHERE user_id = ? AND session_id = ? "
                 f"ORDER BY date DESC LIMIT 1;")
    row = execute_selection_query(sql_query, [user_id, session_id])
    return row[0][0]


def get_history_and_date(user_id):
    sq1_query = f"SELECT content, date FROM {DB_TABLE_USERS_NAME} WHERE user_id = ? AND role = 'assistant';"
    rows = execute_selection_query(sq1_query, [user_id])

    history_list = []
    for row in rows:
        history_list.append({"content": row[0], "date": row[1]})

    return history_list


# Функция для подготовки базы данных
# Создаёт/подключается к бд, добавляет все таблицы, заполняет таблицу с промтами
def prepare_db(clean_if_exists=False):
    create_db()
    create_table(DB_TABLE_USERS_NAME)
    if clean_if_exists:
        clean_table(DB_TABLE_USERS_NAME)
