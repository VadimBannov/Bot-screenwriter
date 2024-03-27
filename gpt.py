import requests
from config import *
import logging

user_data = {}
user_collection = {}


def count_tokens(messages: list) -> int:
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
       "maxTokens": MAX_MODEL_TOKENS,
       "messages": []
    }

    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
            json=data,
            headers=headers
        ).json()["tokens"]
    )


def ask_gpt(collection, mode='continue'):
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 100
        },
        "messages": []
    }
    for row in collection:
        content = row['content']
        # Добавляем дополнительный текст к сообщению пользователя в зависимости от режима
        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + CONTINUE_STORY
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + END_STORY
        data["messages"].append(
                {
                    "role": row["role"],
                    "text": content
                }
            )
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logging.debug(f"Response {response.json()} Status code:{response.status_code} Message {response.text}")
            result = f"Status code {response.status_code}. Подробности см. в журнале."
            return result
        result = response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."

    return result


def create_system_prompt(data, user_id):
    prompt = SYSTEM_PROMPT
    prompt += (f"\nНапиши начало истории в стиле {data[user_id]['genre']} "
               f"с главным героем {data[user_id]['character']}. "
               f"Вот начальный сеттинг: \n{data[user_id]['setting']}. \n"
               "Начало должно быть коротким, 1-3 предложения.\n")
    if data[user_id]['additional_info']:
        prompt += (f"Так же пользователь попросил учесть "
                   f"следующую дополнительную информацию: {data[user_id]['additional_info']}")
    prompt += 'Не пиши никакие подсказки пользователю, что делать дальше. Он сам знает'
    return prompt


def create_new_token():
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(METADATA_URL, headers=headers)
    return response.json()


def main(user_id=1):
    session = 0
    tokens_in_session = 0

    print("Привет! Я помогу тебе составить классный сценарий!")
    genre = input("Для начала напиши жанр, в котором хочешь составить сценарий: ")
    character = input("Теперь опиши персонажа, который будет главным героем: ")
    setting = input("И последнее. Напиши сеттинг, в котором будет жить главный герой: ")

    data = {
        user_id: {
            'genre': genre,
            'character': character,
            'setting': setting,
            'additional_info': ''
        }
    }

    collection = {
        user_id: [
            {'role': 'system', 'content': create_system_prompt(data, user_id)},
        ]
    }

    user_content = input('Напиши начало истории: \n')
    while user_content.lower() != 'end':
        collection[user_id].append({'role': 'user', 'content': user_content})
        tokens = count_tokens(collection[user_id])
        tokens_in_session += tokens
        if tokens_in_session > MAX_TOKENS_IN_SESSION:
            print('Вы вышли за лимит сообщений в рамках диалога')
            break
        assistant_content = ask_gpt(collection[user_id])
        collection[user_id].append({'role': 'assistant', 'content': assistant_content})
        print('YandexGPT: ', assistant_content)
        user_content = input('Напиши продолжение истории. Чтобы закончить введи end: \n')
    session += 1
    if session > MAX_SESSIONS:
        print('Вы превысили лимит сессий')
        return
    assistant_content = ask_gpt(collection[user_id], 'end')
    collection[user_id].append({'role': 'assistant', 'content': assistant_content})

    print('\nВот, что у нас получилось:\n')

    for mes in collection[user_id]:
        print(mes['content'])

    input('\nКонец... ')


if __name__ == "__main__":
    main()
