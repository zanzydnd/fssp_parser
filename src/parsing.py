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
import time
import requests

from dotenv import load_dotenv, find_dotenv
from openpyxl import load_workbook
from models import postgre_db, NotCheckedHuman, FSSPHuman, TaskCode

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93]  # + 1-99


def preparations():
    with postgre_db:
        postgre_db.create_tables([NotCheckedHuman, FSSPHuman, TaskCode])


def get_humans_from_excel(filename):
    workbook = load_workbook(
        filename=os.path.join(os.path.abspath(os.path.curdir), "xls_example", filename))
    sheet = workbook.active
    corteges = sheet["A:B"]
    i = 0
    people = []
    duplicate_people = []
    postgre_db.connect()
    while i < len(corteges[0]):
        map = {}
        try:
            map['lastname'], map['name'], map['secondname'] = str.split(corteges[0][i].value.strip(), " ")
        except ValueError as e:
            i += 1
            continue
        map['birth_date'] = corteges[1][i].value
        try:
            NotCheckedHuman.get(NotCheckedHuman.birth_date == map['birth_date'] and NotCheckedHuman.lastname == map[
                'lastname'] and NotCheckedHuman.name == map['name'] and NotCheckedHuman.secondname == map[
                                    'secondname'])
            duplicate_people.append(map)
        except Exception as e:
            people.append(map)
        i += 1

    if duplicate_people:
        f = open(os.path.join(os.path.abspath(os.path.curdir), "statistics", "duplicates", filename[:-4] + "txt"), "w")
        f.write(str(duplicate_people))
        f.write("\n")
        f.write("Кол-во дупликатов: " + str(len(duplicate_people)))
        f.close()

    with postgre_db.atomic():
        NotCheckedHuman.insert_many(people).execute()


def make_group_request():
    postgre_db.connect()
    try:
        human = NotCheckedHuman.get(NotCheckedHuman.is_checked == False)
    except Exception as e:
        return
    query = []
    for i in range(1, 100):
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": i}}
        query.append(map)
    for num in REGION_NUMBERS:
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": num}}
        query.append(map)
    first = query[:50]
    second = query[50:100]
    third = query[100:]

    response_1 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": first},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})

    response_task = response_1.json()['response']['task']

    while True:
        if not check_is_the_result_ready(response_task):
            time.sleep(20)
        else:
            break

    get_group_result(response=response_1, human=human)

    response_2 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": second},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})
    response_task = response_2.json()['response']['task']
    while True:
        if not check_is_the_result_ready(response_task):
            time.sleep(20)
        else:
            break

    get_group_result(response=response_2, human=human)

    response_3 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": third},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})

    response_task = response_3.json()['response']['task']
    while True:
        if not check_is_the_result_ready(response_task):
            time.sleep(20)
        else:
            break
    get_group_result(response=response_3, human=human)

    human.is_checked = True
    human.save()
    postgre_db.close()


def check_is_the_result_ready(task):
    print("task n:" , task)
    response = requests.get(url=API_URI + "/status",
                            params={"token": os.environ.get("API_KEY"), "task": task})
    status = response.json()['response']['status']
    print("print n status: ", status)
    if status in [0, 3]:
        return True
    return False


# TODO: проверить запись в текст.
def get_group_result(response, human):
    print("from response : ", response.json())
    response_result = requests.get(url=API_URI + "/result",
                                   params={"token": os.environ.get("API_KEY"),
                                           "task": response.json()['response']['task']})
    data_source = []
    print("group resukt: ", response_result.json())
    for result_item in response_result.json()['response']['result']:
        if result_item['result']:
            data = {}
            data['name'] = result_item['query']['params']['firstname']
            data['lastname'] = result_item['query']['params']['lastname']
            data['region'] = result_item['query']['params']['region']
            credentials = result_item['result'][0]['name'].split(" ")
            try:
                data['secondname'] = credentials[2]
            except Exception as e:
                print(e)
                data['secondname'] = None
            try:
                data['date_of_birth'] = credentials[3]
            except Exception as e:
                print(e)
                data['date_of_birth'] = None
            try:
                data['city_info'] = ' '.join(credentials[4:])
            except Exception as e:
                print(e)
                data['city_info'] = None
            data['exe_production'] = result_item['result'][0]['exe_production']
            data['details'] = result_item['result'][0]['details']
            data['subject'] = result_item['result'][0]['subject']
            data['department'] = result_item['result'][0]['department']
            data['bailiff'] = result_item['result'][0]['bailiff']
            data['ip_end'] = result_item['result'][0]['ip_end']
            data_source.append(data)
        else:
            continue

    # postgre_db.connect()

    tsk = TaskCode(human=human, task_code=response.json()['response']['task'], is_executed=True,
                   executed_at=datetime.datetime.now())
    tsk.save()

    f = open(os.path.join(os.path.abspath(os.path.curdir), "statistics", "new_info",
                          response.json()['response']['task'] + ".txt"), "w")
    f.write(str(data_source))
    f.write("\n")
    f.write("Кол-во новых записей: " + str(len(data_source)))
    f.close()

    FSSPHuman.insert_many(data_source).execute()
    # postgre_db.close()


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


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    # preparations()
    make_group_request()
    # get_group_result()
    # make_single_request()
    # get_humans_from_excel("5000 тест фио-дата.xlsx")
