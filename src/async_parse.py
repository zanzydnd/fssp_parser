import datetime
import os
import time
from multiprocessing import Pool

import requests
from dotenv import load_dotenv, find_dotenv

from models import postgre_db, TaskCode, Statistic, FSSPHuman, NotCheckedHuman

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93, 113, 123, 124]  # + 1-99
load_dotenv(find_dotenv())
MONITORING_SERVICE_URL = "http://176.57.217.47/api/parser/report/"


def make_group_request(API_KEY, humans, proxy):
    prx = {"https": proxy}

    while True:
        postgre_db.connect()
        for human in humans:
            query = []

            # human.being_check = True
            # human.save()

            for i in range(1, 93):
                map = {"type": 1, "params": {"firstname": human.name, "lastname": human.lastname, "region": i}}
                query.append(map)
            first = query[:50]
            second = query[50:]

            response_1 = requests.post(url=API_URI + "/search/group",
                                       json={"token": API_KEY, "request": first},
                                       headers={"User-Agent": "PostmanRuntime/7.28.4",
                                                "Content-Type": "application/json"}, proxies=prx)

            print(response_1.json())
            response_task = response_1.json()['response']['task']

            while True:
                if not check_is_the_result_ready(response_task, API_KEY, prx):
                    time.sleep(20)
                else:
                    break

            get_group_result(response=response_1, human=human,prx=prx)

            response_2 = requests.post(url=API_URI + "/search/group",
                                       json={"token": API_KEY, "request": second},
                                       headers={"User-Agent": "PostmanRuntime/7.28.4",
                                                "Content-Type": "application/json"},proxies=prx)
            response_task = response_2.json()['response']['task']

            while True:
                if not check_is_the_result_ready(response_task, API_KEY, prx):
                    time.sleep(20)
                else:
                    break

            get_group_result(response=response_2, human=human, API_KEY=API_KEY,prx=prx)

            human.is_checked = True
            human.save()
            postgre_db.close()


def check_is_the_result_ready(task, API_KEY, prx):
    print("task n: ", task)
    response = requests.get(url=API_URI + "/status",
                            params={"token": API_KEY, "task": task}, proxies=prx)
    try:
        status = response.json()['response']['status']
    except Exception as e:
        return False
    print("print n status: ", status)
    if status in [0, 3]:
        return True
    return False


def get_group_result(response, human, API_KEY, prx):
    print("from response : ", response.json())
    response_result = requests.get(url=API_URI + "/result",
                                   params={"token": API_KEY,
                                           "task": response.json()['response']['task']}, proxies=prx)
    data_source = []
    print("group resukt: ", response_result.json())
    if response_result.json().get('status') == 'error':
        return

    for result_item in response_result.json()['response']['result']:
        if result_item['result']:
            for record in result_item['result']:
                if FSSPHuman.select().where(FSSPHuman.name == record['name'] & FSSPHuman.region == record['region']
                                            & FSSPHuman.exe_production == record['exe_production']
                                            & FSSPHuman.details == record['details']
                                            & FSSPHuman.subject == record['subject']
                                            & FSSPHuman.department == record['department']
                                            & FSSPHuman.bailiff == record['bailiff']
                                            & FSSPHuman.ip_end == record['ip_end']):
                    continue
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


def bridge(corteg):
    make_group_request(corteg[0],corteg[1], corteg[3])

if __name__ == '__main__':
    postgre_db.connect()
    keys = []
    with open(os.path.join(os.path.abspath(os.path.curdir), "keys")) as f:
        for line in f:
            keys.append(line)

    data = []

    butch_size = int(len(
        NotCheckedHuman.select().where(
            NotCheckedHuman.is_checked == False & NotCheckedHuman.being_check == False)) / len(
        keys) + 0.5)

    hum = NotCheckedHuman.select().where(NotCheckedHuman.is_checked == False & NotCheckedHuman.being_check == False)
    i = 0


    proxs = []
    with open(os.path.join(os.path.abspath(os.path.curdir), "proxy.txt")) as f:
        for line in f:
            proxs.append(line)

    for key in keys:
        data.append((key, hum[i * butch_size: i * butch_size + butch_size],proxs[i]))
        i += 1

    postgre_db.close()
    with Pool(len(keys)) as p:
        p.map(bridge, data)
