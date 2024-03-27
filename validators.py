import sqlite3
from database import is_value_in_table, get_size_of_session, get_user_session_id
from config import *


def is_limit_users(db_name, table_name):
    connection = sqlite3.connect(db_name)

    cursor = connection.cursor()
    result = cursor.execute(f'SELECT DISTINCT user_id FROM {table_name};')
    count = 0
    for _ in result:
        count += 1

    connection.close()
    return count >= MAX_USERS


# Функция получает идентификатор пользователя, чата и самого бота, чтобы иметь возможность отправлять сообщения
def is_tokens_limit(user_id, chat_id, bot):

    # Если такого пользователя нет в таблице, ничего делать не будем
    if not is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        return None

    # Берём из таблицы идентификатор сессии
    session_id = get_user_session_id(user_id)
    # Получаем из таблицы размер текущей сессии в токенах
    tokens_of_session = get_size_of_session(user_id, session_id)

    # В зависимости от полученного числа выводим сообщение
    if tokens_of_session >= MAX_TOKENS_IN_SESSION:
        bot.send_message(
            chat_id,
            f'Вы израсходовали все токены в этой сессии. Вы можете начать новую, введя /new_story')
        return None

    elif tokens_of_session + 50 >= MAX_TOKENS_IN_SESSION:  # Если осталось меньше 50 токенов
        bot.send_message(
            chat_id,
            f'Вы приближаетесь к лимиту в {MAX_TOKENS_IN_SESSION} токенов в этой сессии. '
            f'Ваш запрос содержит суммарно {tokens_of_session} токенов.')

    elif tokens_of_session / 2 >= MAX_TOKENS_IN_SESSION:  # Если осталось меньше половины
        bot.send_message(
            chat_id,
            f'Вы использовали больше половины токенов в этой сессии. '
            f'Ваш запрос содержит суммарно {tokens_of_session} токенов.'
        )
    return True
