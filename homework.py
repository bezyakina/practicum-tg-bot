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
BOT_TIME_SLEEP = os.getenv("BOT_TIME_SLEEP")

PRACTICUM_BASE_URL = "https://praktikum.yandex.ru/api/user_api"
HOMEWORK_STATUSES_ENDPOINT = "homework_statuses"

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    if homework.keys() & {"homework_name", "status"}:

        homework_name = homework["homework_name"]
        homework_status = homework["status"]

        if homework_status == "rejected":
            logging.info("Получен статус домашней работы - rejected")
            verdict = "К сожалению в работе нашлись ошибки."

        elif homework_status == "approved":
            logging.info("Получен статус домашней работы - approved")
            verdict = (
                "Ревьюеру всё понравилось, можно приступать к следующему "
                "уроку."
            )

        else:
            print("Неизвестный статус домашнего задания")

        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    print("Произошла ошибка при запросе")


def get_homework_statuses(current_timestamp):
    headers = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

    if isinstance(current_timestamp, (int, str)):
        params = {"from_date": int(current_timestamp)}

        try:
            homework_statuses = requests.get(
                f"{PRACTICUM_BASE_URL}/homework_statuses/",
                headers=headers,
                params=params,
            )
            logging.info("Получен ответ от API практикума")
            return homework_statuses.json()

        # Я правильно понимаю, что нужно описывать множество исключений,
        # например, как тут https://stackoverflow.com/a/47007419 ?
        except Exception as e:
            print(f"Не удалось получить ответ от API практикума, ошибка: {e}")

    else:
        print("Полученый current_timestamp должен имметь тип int или str")


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.info("Started")
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)

            if new_homework.get("homeworks"):
                send_message(
                    parse_homework_status(new_homework.get("homeworks")[0])
                )
                logging.info("Сообщение было успешно отправлено в telegram")
            current_timestamp = new_homework.get("current_date")

            time.sleep(int(BOT_TIME_SLEEP))

        except Exception as e:
            logging.error(f"Бот упал с ошибкой: {e}")
            time.sleep(5)
            continue

    logging.info("Finished")


if __name__ == "__main__":
    main()
