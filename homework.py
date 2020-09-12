import logging
import os
import sys
import time
from logging import handlers

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


LOGFILE = os.getenv("LOGFILE")

log = logging.getLogger("")
log.setLevel(logging.DEBUG)
log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(log_format)
log.addHandler(ch)

fh = handlers.RotatingFileHandler(
    LOGFILE, maxBytes=(1048576 * 5), backupCount=7
)
fh.setFormatter(log_format)
log.addHandler(fh)


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BOT_TIME_SLEEP = os.getenv("BOT_TIME_SLEEP")

PRACTICUM_BASE_URL = "https://praktikum.yandex.ru/api/user_api"
HOMEWORK_STATUSES_ENDPOINT = "homework_statuses"

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    if "homework_name" and "status" not in homework.keys():
        log.error("Произошла ошибка при запросе")
        return (
            f"Произошла ошибка при запросе к API практикума, повторный "
            f"запрос через {int(BOT_TIME_SLEEP) // 60} минут"
        )

    homework_name = homework["homework_name"]
    homework_status = homework["status"]

    homework_statuses = {
        "rejected": "К сожалению в работе нашлись ошибки.",
        "approved": "Ревьюеру всё понравилось, можно "
        "приступать к следующему уроку.",
    }

    if homework_status not in homework_statuses.keys():
        log.error("Неизвестный статус домашнего задания")
        return "Неизвестный статус домашнего задания"

    log.info(f"Получен статус домашней работы - {homework_status}")
    verdict = homework_statuses[homework_status]

    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

    if not isinstance(current_timestamp, (int, str)):
        log.error(
            "Полученый current_timestamp должен имметь тип int или " "str"
        )
        print("Полученый current_timestamp должен имметь тип int или str")

    params = {"from_date": int(current_timestamp)}

    try:
        homework_statuses = requests.get(
            f"{PRACTICUM_BASE_URL}/{HOMEWORK_STATUSES_ENDPOINT}/",
            headers=headers,
            params=params,
        )
        log.info("Получен ответ от API практикума")
        return homework_statuses.json()

    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
    ) as e:
        log.error(f"Не удалось получить ответ от API практикума, ошибка: {e}")
        print(f"Не удалось получить ответ от API практикума, ошибка: {e}")


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    log.info("Started")
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)

            if new_homework.get("homeworks"):
                send_message(
                    parse_homework_status(new_homework.get("homeworks")[0])
                )
                log.info("Сообщение было успешно отправлено в telegram")

            current_timestamp = new_homework.get("current_date")
            time.sleep(int(BOT_TIME_SLEEP))

        except Exception as e:
            log.error(f"Бот упал с ошибкой: {e}")
            time.sleep(5)
            continue

    log.info("Finished")


if __name__ == "__main__":
    main()
