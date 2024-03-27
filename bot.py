import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from database import *
from config import *
import time
import logging
from gpt import (
    user_data,
    create_system_prompt,
    create_new_token,
    user_collection,
    count_tokens,
    ask_gpt
)
from validators import (
    is_limit_users,
    is_tokens_limit
)

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt", filemode="a",
)

prepare_db()
get_all_rows(DB_TABLE_USERS_NAME)


def create_markup(button_labels):
    markup = InlineKeyboardMarkup()
    for label in button_labels:
        markup.add(InlineKeyboardButton(text=label, callback_data=label.lower()))
    return markup


def user_session_exceeded(user_id):
    if get_user_session_id(user_id) < MAX_SESSIONS:
        return None
    else:
        return True


def verification_function_call(call):
    user_id = call.from_user.id

    # token_data = create_new_token()
    # expires_at = time.time() + token_data['expires_in']
    # if expires_at < time.time():
    #     create_new_token()

    if user_id not in user_data:
        bot.send_message(call.message.chat.id, "Ой, упс, о вас нет данных. Вернитесь и укажите снова параметры(")
        time.sleep(1)
        start_for_call_button(call.message)
        return

    if is_limit_users(DB_NAME, DB_TABLE_USERS_NAME):
        bot.send_message(call.message.chat.id,
                         "Бот переполнен пользователем. Пожалуйста, подождите несколько времени.")
        return

    if user_session_exceeded(user_id):
        bot.send_message(call.message.chat.id, "Вы превысили лимит сессий")
        return

    return call


def verification_function_message(message):
    user_id = message.from_user.id

    # token_data = create_new_token()
    # expires_at = time.time() + token_data['expires_in']
    # if expires_at < time.time():
    #     create_new_token()

    if user_id not in user_data:
        bot.send_message(message.chat.id, "Ой, упс, о вас нет данных. Вернитесь и укажите снова параметры(")
        time.sleep(1)
        start_command(message)
        return

    if is_limit_users(DB_NAME, DB_TABLE_USERS_NAME):
        bot.send_message(message.chat.id,
                         "Бот переполнен пользователем. Пожалуйста, подождите несколько времени.")
        return

    if user_session_exceeded(user_id):
        bot.send_message(message.chat.id, "Вы превысили лимит сессий")
        return

    return message


@bot.message_handler(commands=["start"])
def start_command(message):
    user_name, user_id = message.from_user.first_name, message.from_user.id

    if not is_value_in_table(DB_TABLE_USERS_NAME, "user_id", user_id):
        insert_row(
            [
                user_id,
                None,
                None,
                None,
                0,
                0
            ]
        )

    if user_id not in user_data:
        user_data[user_id] = {
            'genre': None,
            'character': None,
            'setting': None,
            'additional_info': ''
        }

    bot.send_photo(message.chat.id, LINK_IMAGE[0], f"Приветствуем {user_name} в бот сценариста "
                                                   f"«Истории Левина»! Чтобы написать историю, нужно указать "
                                                   f"некоторые параметры.\n\nСначала укажите жанр: ",
                   reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))


def start_for_call_button(call):
    user_name, user_id = call.chat.first_name, call.chat.id

    if user_id not in user_data:
        user_data[user_id] = {
            'genre': None,
            'character': None,
            'setting': None,
            'additional_info': ''
        }

    bot.send_photo(call.chat.id, LINK_IMAGE[0], f"Приветствуем {user_name} в бот сценариста "
                                                f"«Истории Левина»! Чтобы написать историю, нужно указать "
                                                f"некоторые параметры.\n\nСначала укажите жанр: ",
                   reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))


@bot.message_handler(commands=['debug'])
def debug_command(message):
    with open("log_file.txt", "r", encoding="latin1") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, "📚Инструкция по использованию бота «Истории Левина»\n\n"
                                      "1. После нажатия старт бот попросит указать жанр, главного героя и сеттинг "
                                      "твоей истории. Выберите ответы из предложенных. Можете добавить дополнительную "
                                      "информацию или пропустить этот шаг\n"
                                      "2. Подтвердите выбор. Проверьте, что все параметры указаны верно\n"
                                      "3. Начните писать историю, а бот будет генерировать продолжение истории. Когда "
                                      "закончите, напишите «Хватит» или используйте команду /end_dialog\n"
                                      "4. Используйте команды /whole_story для просмотра всех историй, /all_tokens для "
                                      "просмотра количества сессий и токенов, /new_story для создания новой истории\n\n"
                                      "Но помните, использование бота ограничено тремя сессиями, в каждой из которых "
                                      "доступно 800 токенов.")
    return


@bot.message_handler(commands=["about"])
def help_command(message):
    bot.send_message(message.chat.id, "🤖Описание бота:\n\n"
                                      "Этот бот-сценарист предназначен для написания историй с помощью заданных "
                                      "параметров. Вы можете выбрать жанр, главного героя и сеттинг для истории, а "
                                      "также добавить дополнительную информацию. После подтверждения параметров, бот "
                                      "предлагает начать писать историю, а затем генерирует уникальную историю. Вы "
                                      "можете просматривать свои старые истории и контролировать баланс токенов. "
                                      "Бот обрабатывает некорректные ваши действия, чтобы обеспечить плавный и "
                                      "невероятный опыт.")
    return


@bot.message_handler(commands=["setting_parameters"])
def command_setting_parameters(message):
    user_id = message.from_user.id

    if verification_function_message(message) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return
    bot.send_message(message.chat.id, "Вы уже установили все параметры.")
    confirming_message(message)


@bot.message_handler(commands=["end_dialog"])
def command_end_dialog(message):
    bot.send_message(message.chat.id, "Вы не в процессе сочинения истории.")


@bot.message_handler(commands=["new_story"])
def command_new_story(message):
    user_id = message.from_user.id

    user_data[user_id] = {
        'genre': None,
        'character': None,
        'setting': None,
        'additional_info': ''
    }

    bot.send_message(message.chat.id, "Хорошо! Напишите новую историю :)")
    time.sleep(1)
    start_command(message)

    return


@bot.message_handler(commands=["whole_story"])
def command_whole_story(message):
    user_id = message.from_user.id

    user_all_history = get_history_and_date(user_id)

    if user_all_history:
        history_text = ""
        for history_item in user_all_history:
            history_text += f"{history_item['date']}: ({history_item['content']})\n"
        bot.send_message(message.chat.id, f"Ваши все истории:\n{history_text}")
    else:
        bot.send_message(message.chat.id, "У вас нет истории запросов.")

    return


@bot.message_handler(commands=["all_tokens"])
def command_all_tokens(message):
    user_id = message.from_user.id

    user_all_session = get_user_session_id(user_id)
    user_all_tokens = get_size_of_session(user_id, user_all_session)

    if user_all_session >= MAX_SESSIONS:
        sessions_text = "у вас не остались сессии."
    else:
        sessions_text = f"{user_all_session} из {MAX_SESSIONS};"
    if user_all_tokens >= MAX_TOKENS_IN_SESSION:
        tokens_text = "у вас не остались токены."
    else:
        tokens_text = f"{user_all_tokens} из {MAX_TOKENS_IN_SESSION};"

    bot.send_message(message.chat.id, f"Ваши все сессии и токены:\n\n"
                                      f"Сессии: {sessions_text}\n"
                                      f"Токены: {tokens_text}")
    return


@bot.callback_query_handler(func=lambda call: call.data in ["хоррор", "вестерн", "фантастика", "комедия"])
def get_genre(call):
    call_button, user_id = call.data, call.from_user.id

    if verification_function_call(call) is None:
        return

    if call_button == 'хоррор':
        user_data[user_id]["genre"] = "Хоррор"
    elif call_button == 'вестерн':
        user_data[user_id]["genre"] = "Вестерн"
    elif call_button == 'фантастика':
        user_data[user_id]["genre"] = "Фантастика"
    else:
        user_data[user_id]["genre"] = "Комедия"

    bot.send_photo(call.message.chat.id, LINK_IMAGE[1], "Отлично! А теперь выберите твоего главного героя:\n\n"
                                                        "Описание персонажей:\n"
                                                        "Сьюзи - молодая студентка, недавно переехавшая в странный "
                                                        "колледж, где начинают происходить паранормальные явления;\n"
                                                        "Джек - одинокий ковбой, который пытается отомстить за своего "
                                                        "отца;\n"
                                                        "Майя - ученый, который работает над созданием дома, способного"
                                                        " останавливать время;\n"
                                                        "Стив - неуклюжий парень, который постоянно попадает в "
                                                        "нелепые ситуации.",
                   reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))


@bot.callback_query_handler(func=lambda call: call.data in ['сьюзи', 'джек', 'майя', 'стив'])
def get_character(call):
    call_button, user_id = call.data, call.from_user.id

    if verification_function_call(call) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(call.message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return

    if call_button == 'сьюзи':
        user_data[user_id]["character"] = ("Сьюзи - молодая студентка, недавно переехавшая в странный "
                                           "колледж, где начинают происходить паранормальные явления")
    elif call_button == 'джек':
        user_data[user_id]["character"] = "Джек - одинокий ковбой, который пытается отомстить за своего отца"
    elif call_button == 'майя':
        user_data[user_id]["character"] = ("Майя - ученый, который работает над созданием дома, способного "
                                           "останавливать время")
    else:
        user_data[user_id]["character"] = "Стив - неуклюжий парень, который постоянно попадает в нелепые ситуации"

    bot.send_photo(call.message.chat.id, LINK_IMAGE[2], "Класс! И последнее, выберите сеттинг: ",
                   reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога", "Подводный город",
                                               "Офис"]))


@bot.callback_query_handler(func=lambda call: call.data in ['старое здание на окраине города', 'железная дорога',
                                                            'подводный город', 'офис'])
def get_setting(call):
    call_button, user_id = call.data, call.from_user.id

    if verification_function_call(call) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(call.message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(call.message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return

    if call_button == 'старое здание на окраине города':
        user_data[user_id]["setting"] = "Старое здание на окраине города"
    elif call_button == 'железная дорога':
        user_data[user_id]["setting"] = "Железная дорога"
    elif call_button == 'подводный город':
        user_data[user_id]["setting"] = "Подводный город"
    else:
        user_data[user_id]["setting"] = "Офис"

    bot.send_message(call.message.chat.id, "Напишите дополнительную информацию или "
                                           "пропустите написав «Пропустить» ",
                     reply_markup=create_markup(['Бот отправляет ошибку']))
    bot.register_next_step_handler(call.message, get_additional_information)


@bot.callback_query_handler(func=lambda call: call.data in ['бот отправляет ошибку'])
def bot_sends_an_error(call):
    bot.send_message(call.message.chat.id, "Понял вас! Попробуйте снова написать: ",
                     reply_markup=create_markup(['Бот отправляет ошибку']))
    bot.register_next_step_handler(call.message, get_additional_information)
    return


def get_additional_information(message):
    message_text, user_id = message.text, message.chat.id

    if verification_function_message(message) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return

    if message.content_type != "text":
        bot.send_message(message.chat.id, "Отправь имя в виде текстового сообщения: ")
        bot.register_next_step_handler(message, get_additional_information)
        return

    if message.text.lower() == "пропустить":
        confirming_message(message)
        return

    try:
        if int(message_text):
            bot.send_message(message.chat.id, "Пожалуйста, введите имя героя, а не число/цифру.")
            bot.register_next_step_handler(message, get_additional_information)
            return
    except ValueError:
        try:
            if float(message_text):
                bot.send_message(message.chat.id, "Пожалуйста, введите имя героя, а не число/цифру.")
                bot.register_next_step_handler(message, get_additional_information)
                return
        except ValueError:
            additional_information = message_text
            user_data[user_id]["additional_info"] = additional_information
            confirming_message(message)


def confirming_message(message):
    user_id = message.from_user.id

    if verification_function_message(message) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return

    genre, character, setting, additional_info = (user_data[user_id]["genre"],
                                                  user_data[user_id]["character"],
                                                  user_data[user_id]["setting"],
                                                  user_data[user_id]["additional_info"])

    if additional_info == "":
        additional_info = "Дополнительная информация нет"

    bot.send_message(message.chat.id, f"Вы действительно хотите применить эти параметры?\n\n"
                                      f"Жанр: ({genre});\n"
                                      f"Главный герой: ({character});\n"
                                      f"Сеттинг: ({setting});\n"
                                      f"Дополнительная информация: ({additional_info})",
                     reply_markup=create_markup(["Применить", "Изменить"]))


@bot.callback_query_handler(func=lambda call: call.data in ['применить', 'изменить'])
def apply_or_change(call):

    call_button, user_id = call.data, call.from_user.id

    if verification_function_call(call) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(call.message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(call.message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(call.message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return

    if call_button == "применить":
        session_id = get_user_session_id(user_id)
        user_tokens = 0
        user_session = session_id + 1
        user_collection[user_id] = [
            {'role': 'system', 'content': create_system_prompt(user_data, user_id)},
        ]

        insert_row(
            [
                user_id,
                'system',
                create_system_prompt(user_data, user_id),
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                user_tokens,
                user_session
            ]
        )
        if is_tokens_limit(user_id, call.message.chat.id, bot) is None:
            return
        bot.send_message(call.message.chat.id, "Напиши начало истории: ")
        bot.register_next_step_handler(call.message, get_promt)
    else:
        user_data[user_id] = {
            'genre': None,
            'character': None,
            'setting': None,
            'additional_info': ''
        }
        time.sleep(1)
        start_for_call_button(call.message)
        return


def get_promt(message):

    message_text, user_id = message.text, message.from_user.id

    if verification_function_call(message) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return

    if message.content_type != "text":
        bot.send_message(message.chat.id, "Отправь промт текстовым сообщением")
        bot.register_next_step_handler(message, get_promt)
        return

    user_promt = message_text
    if user_promt.lower() == 'хватит' or user_promt.lower() == '/end_dialog':
        bot.send_message(message.chat.id,
                         'Ух ты! Вы уже написали свою историю, а теперь выберите одно из трех действий.',
                         reply_markup=create_markup(["Написать новую историю", "Просмотреть все свои истории",
                                                     "Посмотреть свои токены"]))
        return
    user_collection[user_id].append({'role': 'user', 'content': user_promt})
    tokens = count_tokens(user_collection[user_id])
    user_session = get_user_session_id(user_id)
    user_tokens = (get_size_of_session(user_id, user_session))
    user_tokens += tokens
    insert_row(
        [
            user_id,
            'user',
            user_promt,
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            user_tokens,
            user_session
        ]
    )
    if is_tokens_limit(user_id, message.chat.id, bot) is None:
        bot.send_message(message.chat.id,
                         'Ух ты! Вы уже написали свою историю, а теперь выберите одно из трех действий.',
                         reply_markup=create_markup(["Написать новую историю", "Просмотреть все свои истории",
                                                     "Посмотреть свои токены"]))
        return
    assistant_content = ask_gpt(user_collection[user_id])
    user_collection[user_id].append({'role': 'assistant', 'content': assistant_content})
    insert_row(
        [
            user_id,
            'assistant',
            assistant_content,
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            user_tokens,
            user_session
        ]
    )
    bot.send_message(message.chat.id, f'YandexGPT: {assistant_content}')
    time.sleep(2)
    bot.send_message(message.chat.id, 'Напиши продолжение истории. Чтобы закончить напишите «Хватит» ')
    bot.register_next_step_handler(message, get_promt)
    return


@bot.callback_query_handler(func=lambda call: call.data in ["написать новую историю", "просмотреть все свои истории",
                                                            "посмотреть свои токены"])
def crossroads_messages(call):
    call_button, user_id = call.data, call.from_user.id

    if verification_function_call(call) is None:
        return

    if user_data[user_id]["genre"] is None:
        bot.send_message(call.message.chat.id, "Сначала укажите жанр: ",
                         reply_markup=create_markup(["Хоррор", "Вестерн", "Фантастика", "Комедия"]))
        return
    elif user_data[user_id]["character"] is None:
        bot.send_message(call.message.chat.id, "Сначла выберите твоего главного героя: ",
                         reply_markup=create_markup(["Сьюзи", "Джек", "Майя", "Стив"]))
        return
    elif user_data[user_id]["setting"] is None:
        bot.send_message(call.message.chat.id, "Сначала выберите сеттинг: ",
                         reply_markup=create_markup(["Старое здание на окраине города", "Железная дорога",
                                                     "Подводный город", "Офис"]))
        return

    if call_button == "написать новую историю":
        user_data[user_id] = {
            'genre': None,
            'character': None,
            'setting': None,
            'additional_info': ''
        }

        bot.send_message(call.message.chat.id, "Хорошо! Напишите новую историю :)")
        time.sleep(1)
        start_for_call_button(call)

        return
    elif call_button == "просмотреть все свои истории":
        user_all_history = get_history_and_date(user_id)

        if user_all_history:
            history_text = ""
            for history_item in user_all_history:
                history_text += f"{history_item['date']}: ({history_item['content']})\n"
            bot.send_message(call.message.chat.id, f"Ваши все истории:\n{history_text}")
        else:
            bot.send_message(call.message.chat.id, "У вас нет истории запросов.")

        return
    else:
        user_all_session = get_user_session_id(user_id)
        user_all_tokens = get_size_of_session(user_id, user_all_session)

        if user_all_session >= MAX_SESSIONS:
            sessions_text = "у вас не остались сессии."
        else:
            sessions_text = f"{user_all_session} из {MAX_SESSIONS};"
        if user_all_tokens >= MAX_TOKENS_IN_SESSION:
            tokens_text = "у вас не остались токены."
        else:
            tokens_text = f"{user_all_tokens} из {MAX_TOKENS_IN_SESSION};"

        bot.send_message(call.message.chat.id, f"Ваши все сессии и токены:\n\n"
                                               f"Сессии: {sessions_text}\n"
                                               f"Токены: {tokens_text}")
        return


@bot.message_handler()
@bot.message_handler(content_types=['photo', 'document'])
def strange_message(message):
    bot.send_message(message.chat.id, "Я не понял вашего действия, выберите внутреннюю кнопку!")
    return


bot.polling()
