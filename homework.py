import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    format="Date-Time : %(asctime)s : Line No. : %(lineno)d " "- %(message)s",
    level=logging.INFO,
)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PRACTICUM_BASE_URL = "https://praktikum.yandex.ru/api/user_api"


def parse_homework_status(homework):
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status == "rejected":
        logging.info("Получен статус домашней работы - rejected")
        verdict = "К сожалению в работе нашлись ошибки."
    else:
        logging.info("Получен статус домашней работы - aproved")
        verdict = (
            "Ревьюеру всё понравилось, можно приступать к следующему " "уроку."
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
    params = {"from_date": current_timestamp}
    try:
        homework_statuses = requests.get(
            f"{PRACTICUM_BASE_URL}/homework_statuses/",
            headers=headers,
            params=params,
        )
        logging.info("Получен ответ от API практикума")
    except Exception as e:
        logging.error(
            f"Не удалось получить ответ от API практикума, ошибка: {e}"
        )
        print(f"Не удалось получить ответ от API практикума, ошибка: {e}")
    return homework_statuses.json()


def send_message(message):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.info("Started")
    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get("homeworks"):
                send_message(
                    parse_homework_status(new_homework.get("homeworks")[0])
                )
                logging.debug("Сообщение было успешно отправлено в telegram")
            current_timestamp = new_homework.get(
                "current_date"
            )  # обновить timestamp
            time.sleep(1200)  # опрашивать раз в пять минут

        except Exception as e:
            logging.error(f"Бот упал с ошибкой: {e}")
            print(f"Бот упал с ошибкой: {e}")
            time.sleep(5)
            continue

    logging.info("Finished")


if __name__ == "__main__":
    main()
