"""
Максимальное число подзапросов в групповом запросе— 50
(если требуется отправить большее число, следует разбивать запрос на несколько).

Максимальное число одиночных запросов в час — 100.
(Ограничение на одиночные запросы считается, как минус час от текущего времени)

Максимальное число одиночных запросов в сутки — 1000.
(Ограничение на одиночные запросы считается, как минус сутки от текущего времени)

Максимальное число групповых запросов в сутки — 5000.

Срок хранения результатов запроса (промежуток между обращениями к методам /search/ и методу /result) — 24 часа.
"""

# Каждый день отправляем по 5000 групповых запросов, если приходит полный ответ ,
# то получаем 5000 * 50 = 250 000 человек
# Так же каждый день отправляем по 1000 одиночных запросов( каждый час по 100 , итого : 10 часов)
# Получаем 1000 человек.

# Записываем task_code в отдельную таблцу и прогоняем каждые 12 часов - невыполненные запросы.
# Результат записываем в бд
import os
import time
from pprint import pprint

import requests
from dotenv import load_dotenv, find_dotenv

from models import postgre_db, NotCheckedHuman, FSSPHuman, TaskCode

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93]  # + 1-99


def preparations():
    with postgre_db:
        postgre_db.create_tables([NotCheckedHuman, FSSPHuman, TaskCode])


def make_group_request():
    postgre_db.connect()
    human = NotCheckedHuman.get(NotCheckedHuman.is_checked == False)
    query = []
    for i in range(1, 100):
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": i}}
        query.append(map)
    for num in REGION_NUMBERS:
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": num}}
        query.append(map)
    first = query[:50]
    second = query[50:100]
    third = query[101:]
    # pprint(first)
    # pprint({"token": os.environ.get("API_KEY"), "request": first})
    response_1 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": first},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})
    time.sleep(100)
    response_2 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": second},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})
    time.sleep(200)
    response_3 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": third},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})
    print(response_1.json())
    tsk = TaskCode(human=human, task_code=response_1.json()['response']['task'])
    tsk.save()
    print(response_2.json())
    tsk = TaskCode(human=human, task_code=response_2.json()['response']['task'])
    tsk.save()
    print(response_3.json())
    tsk = TaskCode(human=human, task_code=response_3.json()['response']['task'])
    tsk.save()
    human.is_checked = True
    human.save()
    postgre_db.close()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    make_group_request()
