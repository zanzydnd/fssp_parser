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
MONITORING_SERVICE_URL = "http://176.57.217.47/api/parser/report/"


def send_status_to_monitoring_service(status, description):
    body = {"token": os.environ.get("CHECK_PARSER_TOKEN"), "status": status, "description": description,
            "name": os.environ.get("PARSER_NAME")}
    response_from_check_service = requests.post(url=MONITORING_SERVICE_URL + os.environ.get("PARSER_NAME"), json=body)


def check_is_there_new_human_to_check():
    try:
        human = NotCheckedHuman.get(
            NotCheckedHuman.is_checked == False and NotCheckedHuman.being_check == False)
        return human
    except Exception as e:
        f = open(os.path.join(os.path.abspath(os.path.curdir), "log_file.txt"), "w",
                 encoding="utf-8")
        f.write(str(datetime.date.today()) + " - " + "Закончились люди в бд.")
        f.close()
        send_status_to_monitoring_service("not_critical", "Нет новых людей в базе.")
        return "no_humans"


def make_group_request():
    postgre_db.connect()

    while True:
        human_or_not = check_is_there_new_human_to_check()
        if human_or_not == "no_humans":
            time.sleep(20)
        else:
            human = human_or_not
            break
    query = []
    human.being_check = True
    human.save()
    for i in range(1, 93):
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": i}}
        query.append(map)
    first = query[:50]
    second = query[50:]

    # os.environ['https_proxy'] = sys.argv[2] #"e_blinova_tiwo_ru:9cb089306d@213.166.91.67:30011"
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
    return "Done"


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
    if response_result.json().get('status') == 'error':
        return
    for result_item in response_result.json()['response']['result']:
        if result_item['result']:
            for record in result_item['result']:
                data = {}
                data['region'] = result_item['query']['params']['region']
                data['name'] = record['name']
                data['exe_production'] = record['exe_production']
                data['details'] = record['details']
                data['subject'] = record['subject']
                data['department'] = record['department']
                data['bailiff'] = record['bailiff']
                data['ip_end'] = record['ip_end']
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
start = datetime.datetime.now()
while count < 4996:
    return_string = make_group_request()
    now = datetime.datetime.now()
    if (now - start).days >= 1:
        count = 0
        start = datetime.datetime.now()
        send_status_to_monitoring_service("ok", "Ok")
    count += 2
    if count == 4995:
        count = 0
        send_status_to_monitoring_service("ok", "Ok")
        time.sleep(86400)
