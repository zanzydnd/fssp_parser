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
        for j in range(1, 100):
            map = {}
            try:
                map['lastname'], map['name'], map['secondname'] = str.split(corteges[0][i].value.strip(), " ")
            except ValueError as e:
                i += 1
                continue
            map['birth_date'] = corteges[1][i].value
            map['region'] = j
            try:
                NotCheckedHuman.get(NotCheckedHuman.birth_date == map['birth_date'] and NotCheckedHuman.lastname == map[
                    'lastname'] and NotCheckedHuman.name == map['name'] and NotCheckedHuman.secondname == map[
                                        'secondname'])
                duplicate_people.append(map)
            except Exception as e:
                people.append(map)
        for num in REGION_NUMBERS:
            map = {}
            try:
                map['lastname'], map['name'], map['secondname'] = str.split(corteges[0][i].value.strip(), " ")
            except ValueError as e:
                i += 1
                continue
            map['birth_date'] = corteges[1][i].value
            map['region'] = num

            try:
                NotCheckedHuman.get(NotCheckedHuman.birth_date == map['birth_date'] and NotCheckedHuman.lastname == map[
                    'lastname'] and NotCheckedHuman.name == map['name'] and NotCheckedHuman.secondname == map[
                                        'secondname'])
                duplicate_people.append(map)
            except Exception as e:
                people.append(map)
        i += 1

    if duplicate_people:
        f = open(os.path.join(os.path.abspath(os.path.curdir), "statistics", filename), "w")
        f.write(duplicate_people)
        f.write("\n")
        f.write("Кол-во дупликатов: " + str(len(duplicate_people)))
        f.close()

    with postgre_db.atomic():
        NotCheckedHuman.insert_many(people).execute()


def make_group_request():
    postgre_db.connect()
    humans = NotCheckedHuman.select().where(NotCheckedHuman.is_checked == False).limit(50)
    query = []
    query_ids = []
    for human in humans:
        query_ids.append(human.id)
        map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": human.region}}
        query.append(map)

    response_1 = requests.post(url=API_URI + "/search/group",
                               json={"token": os.environ.get("API_KEY"), "request": query},
                               headers={"User-Agent": "PostmanRuntime/7.28.4", "Content-Type": "application/json"})

    tsk = TaskCode(not_checked_humans_ids=query_ids, task_code=response_1.json()['response']['task'])
    tsk.save()

    execution = NotCheckedHuman.update(validated=True).where(NotCheckedHuman.id.in_(query_ids))
    execution.execute()
    postgre_db.close()


def get_group_result():
    postgre_db.connect()
    task_code = TaskCode.get(TaskCode.is_executed == False)
    response = requests.get(url=API_URI + "/result",
                            params={"token": os.environ.get("API_KEY"), "task": task_code.task_code})
    postgre_db.close()
    data_source = []

    for result_item in response.json()['response']['result']:
        if result_item['result']:
            data = {}
            data['name'] = result_item['query']['params']['firstname']
            data['lastname'] = result_item['query']['params']['lastname']
            data['region'] = result_item['query']['params']['region']
            credentials = result_item['result'][0]['name'].split(" ")
            print(credentials)
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

    postgre_db.connect()
    FSSPHuman.insert_many(data_source).execute()
    task_code.is_executed = True
    task_code.executed_at = datetime.datetime.now()
    task_code.save()
    postgre_db.close()


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
    # make_group_request()
    # get_group_result()
    # make_single_request()
    get_humans_from_excel("5000 тест фио-дата.xlsx")
