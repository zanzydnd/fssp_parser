from dotenv import load_dotenv, find_dotenv
import aiohttp

from models_tortoise import FSSPHuman

API_URI = "https://api-ip.fssp.gov.ru/api/v1.0"
REGION_NUMBERS = [102, 116, 125, 138, 150, 154, 159, 161, 163, 173, 174, 118, 121, 93, 113, 123, 124]  # + 1-99
load_dotenv(find_dotenv())
MONITORING_SERVICE_URL = "http://176.57.217.47/api/parser/report/"
API_KEY = ''


async def is_exists(instance: dict):
    return await FSSPHuman.exists(**instance)


async def is_result_ready(task):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=API_URI + "/status", params={"token": API_KEY, "task": task}) as resp:
            try:
                response_json = await resp.json()
                status = response_json['response']['status']
                if status in [0, 3]:
                    return True
                return False
            except Exception as e:
                print(e)
                return False

async def make_request():
    pass