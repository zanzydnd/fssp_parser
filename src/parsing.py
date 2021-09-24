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
import datetime
import os
import sys
import time
import requests

from dotenv import load_dotenv, find_dotenv
from models import postgre_db, NotCheckedHuman, FSSPHuman, TaskCode, Statistic

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93, 113, 123, 124]  # + 1-99
load_dotenv(find_dotenv())
API_KEY = sys.argv[1]

def make_group_request():
    postgre_db.connect()
    try:
        human = NotCheckedHuman.get(NotCheckedHuman.is_checked == False and NotCheckedHuman.being_check == False)
    except Exception as e:
        return
    query = []
    human.being_check = True
    human.save()
    for i in range(1, 93):
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": i}}
        query.append(map)
    first = query[:50]
    second = query[50:]

    #os.environ['https_proxy'] = sys.argv[2] #"e_blinova_tiwo_ru:9cb089306d@213.166.91.67:30011"
    response_1 = requests.post(url=API_URI + "/search/group",
                               json={"token": API_KEY, "request": first},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})

    print(response_1.json())
    response_task = response_1.json()['response']['task']

    while True:
        if not check_is_the_result_ready(response_task):
            time.sleep(20)
        else:
            break

    get_group_result(response=response_1, human=human)

    response_2 = requests.post(url=API_URI + "/search/group",
                               json={"token": API_KEY, "request": second},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})
    response_task = response_2.json()['response']['task']

    while True:
        if not check_is_the_result_ready(response_task):
            time.sleep(20)
        else:
            break

    get_group_result(response=response_2, human=human)

    human.is_checked = True
    human.save()
    postgre_db.close()


def check_is_the_result_ready(task):
    print("task n: ", task)
    response = requests.get(url=API_URI + "/status",
                            params={"token": API_KEY, "task": task})
    status = response.json()['response']['status']
    print("print n status: ", status)
    if status in [0, 3]:
        return True
    return False


def get_group_result(response, human):
    print("from response : ", response.json())
    response_result = requests.get(url=API_URI + "/result",
                                   params={"token": API_KEY,
                                           "task": response.json()['response']['task']})
    data_source = []
    print("group resukt: ", response_result.json())
    for result_item in response_result.json()['response']['result']:
        if result_item['result']:
            data = {}
            data['region'] = result_item['query']['params']['region']
            data['name'] = result_item['query']['params']['region']
            data['exe_production'] = result_item['result'][0]['exe_production']
            data['details'] = result_item['result'][0]['details']
            data['subject'] = result_item['result'][0]['subject']
            data['department'] = result_item['result'][0]['department']
            data['bailiff'] = result_item['result'][0]['bailiff']
            data['ip_end'] = result_item['result'][0]['ip_end']
            data_source.append(data)
        else:
            continue


    tsk = TaskCode(human=human, task_code=response.json()['response']['task'], is_executed=True,
                   executed_at=datetime.datetime.now())
    tsk.save()

    f = Statistic(task=tsk, num_of_new_records=len(data_source))
    f.save()
    FSSPHuman.insert_many(data_source).execute()


# TODO: переделать
def make_single_request():
    postgre_db.connect()
    human = NotCheckedHuman.get(NotCheckedHuman.is_checked == False)
    map = {"token": os.environ.get("API_KEY"), "firstname": human.name, "lastname": human.lastname,
           "region": human.region}
    response = requests.get(url=API_URI + "/search/physical", params=map,
                            headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})

    task_code = response.json()['response']['task']
    tsk = TaskCode(not_checked_humans_ids=[human.id], task_code=task_code)
    tsk.save()
    human.is_checked = True
    human.save()
    postgre_db.close()


count = 0
while count < 4996:
    make_group_request()
    count += 3
    if count == 4995:
        count = 0
        time.sleep(86400)
