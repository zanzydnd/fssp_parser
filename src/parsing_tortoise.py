import asyncio

import requests
from dotenv import load_dotenv, find_dotenv
import aiohttp
from tortoise import Tortoise

from core import Config
from models_tortoise import FSSPHuman, NotCheckedHuman

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93, 113, 123, 124]  # + 1-99
load_dotenv(find_dotenv())
MONITORING_SERVICE_URL = "http://176.57.217.47/api/parser/report/"
API_KEY = '9imsWPN9EVLM'


async def is_exists(instance: dict):
    return await FSSPHuman.exists(**instance)


async def is_result_ready(task):
    response = requests.get(url=API_URI + "/status", params={"token": API_KEY, "task": task})
    try:
        response_json = response.json()
        print(response_json)
        status = response_json['response']['status']
        if status in [0, 3]:
            return True
        return False
    except Exception as e:
        print(e)
        return False
    # async with aiohttp.ClientSession(trust_env=True) as session:
    #     async with session.get(url=API_URI + "/status", params={"token": API_KEY, "task": task}) as resp:
    #         try:
    #             response_json = await resp.json()
    #             print(response_json)
    #             status = response_json['response']['status']
    #             if status in [0, 3]:
    #                 return True
    #             return False
    #         except Exception as e:
    #             print(e)
    #             return False


async def get_group_result(task):
    resp = requests.get(url=API_URI + "/result",
                        params={"token": API_KEY, "task": task})
    data = []
    response_json = resp.json()
    print(response_json)
    if response_json.get('status') == 'error':
        return

    for result_it in response_json['response']['result']:
        if result_it.get('result'):
            for record in result_it.get('result'):
                if not await is_exists(record):
                    data.append(FSSPHuman(**record))
        else:
            continue
    await FSSPHuman.bulk_create(data)
    print('created')
    # async with aiohttp.ClientSession(trust_env=True) as session:
    #     async with session.get(url=API_URI + "/result",
    #                            params={"token": API_KEY, "task": task}) as resp:
    #
    #         data = []
    #         response_json = await resp.json()
    #         print(response_json)
    #         if response_json.get('status') == 'error':
    #             return
    #
    #         for result_it in response_json['response']['result']:
    #             if result_it.get('result'):
    #                 for record in result_it.get('result'):
    #                     if not await is_exists(record):
    #                         data.append(FSSPHuman(**record))
    #             else:
    #                 continue
    #         await FSSPHuman.bulk_create(data)
    #         print('created')


async def make_request(humans):
    for human in humans:
        query = []

        for i in range(1, 93):
            map = {"type": 1,
                   "params": {"firstname": human.name, "lastname": human.lastname,
                              "birthdate": human.birth_date.strftime("%d.%m.%Y"),
                              "region": i}}
            query.append(map)

        first = query[:50]
        second = query[50:]

        resp = requests.post(url=API_URI + "/search/group",
                             json={"token": API_KEY, "request": first})
        resp_json = resp.json()
        print(resp_json)
        try:
            task_uuid = resp_json['response']['task']

            while not await is_result_ready(task_uuid):
                await asyncio.sleep(20)

            await get_group_result(task_uuid)


        except Exception as e:
            print(e)
        # async with aiohttp.ClientSession(trust_env=True) as session:
        #     async with session.post(url=API_URI + "/search/group",
        #                             data={"token": API_KEY, "request": first}) as resp:
        #
        #         resp_json = await resp.json()
        #         print(resp_json)
        #         try:
        #             task_uuid = resp_json['response']['task']
        #
        #             while not await is_result_ready(task_uuid):
        #                 await asyncio.sleep(20)
        #
        #             await get_group_result(task_uuid)
        #
        #
        #         except Exception as e:
        #             print(e)
        resp_2 = requests.post(url=API_URI + "/search/group",
                               json={"token": API_KEY, "request": second})

        resp_json_2 = resp_2.json()
        print(resp_json_2)
        try:
            task_uuid = resp_json_2['response']['task']

            while not await is_result_ready(task_uuid):
                await asyncio.sleep(20)

            await get_group_result(task_uuid)
        except Exception as e:
            print(e)
        # async with aiohttp.ClientSession(trust_env=True) as session_2:
        #     async with session_2.post(url=API_URI + "/search/group",
        #                               data={"token": API_KEY, "request": second}, ) as resp_2:
        #         resp_json_2 = await resp_2.json()
        #         print(resp_json_2)
        #         try:
        #             task_uuid = resp_json_2['response']['task']
        #
        #             while not await is_result_ready(task_uuid):
        #                 await asyncio.sleep(20)
        #
        #             await get_group_result(task_uuid)
        #         except Exception as e:
        #             print(e)


async def run_parser():
    config = Config()
    await Tortoise.init(
        db_url=str(config.DATABASE_URL()),
        modules={'models': ['models_tortoise.humans', ]}
    )
    count = await NotCheckedHuman.filter(name__not_isnull=True, lastname__not_isnull=True,
                                         birth_date__not_isnull=True).count()
    print(count)
    limit = int(count * 0.3)
    offset_max = count // limit
    print(offset_max)
    while True:
        for i in range(offset_max):
            humans = await NotCheckedHuman.filter(name__not_isnull=True, lastname__not_isnull=True,
                                                  birth_date__not_isnull=True).limit(limit).offset(i)
            await make_request(humans)


asyncio.run(run_parser())
