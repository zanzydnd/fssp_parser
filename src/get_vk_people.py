import os
import sys
import csv
import datetime
import requests

from dotenv import load_dotenv, find_dotenv
from models import postgre_db, NotCheckedHuman

load_dotenv(find_dotenv())


def get_it(filename: str, token: str):
    with open(os.path.join(os.path.abspath(os.path.curdir), "xls_example", filename), newline='') as file:
        reader = csv.reader(file)
        data = []
        for row in reader:
            id = row[1]
            response_1 = requests.post(url="https://api.vk.com/method/users.get",
                                       params={"v": "5.131", "fields": "bdate", "name_case": "nom", "user_ids": id,
                                               "access_token": token},
                                       headers={"User-Agent": "PostmanRuntime/7.28.4",
                                                "Content-Type": "application/json"})

            print(response_1.content)

            for entity in response_1.json()['response']:
                try:
                    day, month, year = ["0" + i if len(i) == 1 else i for i in entity['bdate'].split(".")]
                    print(day, month, year)
                    map = {
                        "lastname": entity['last_name'],
                        "name": entity['first_name'],
                        "birth_date": datetime.datetime.strptime(f'{day}.{month}.{year}', '%d.%m.%Y')
                    }
                    # data.append(map)
                    postgre_db.connect()
                    with postgre_db.atomic():
                        NotCheckedHuman.insert(map).execute()
                    postgre_db.close()
                except Exception as e:
                    print(e)
                # if len(data) >= 50000:
                #     postgre_db.connect()
                #     with postgre_db.atomic():
                #         NotCheckedHuman.insert_many(data).execute()
                #     postgre_db.close()
                #     data.clear()

        # if data:
        #     postgre_db.connect()
        #     with postgre_db.atomic():
        #         NotCheckedHuman.insert_many(data).execute()
        #     postgre_db.close()
        #     data.clear()


get_it(sys.argv[1], sys.argv[2])
