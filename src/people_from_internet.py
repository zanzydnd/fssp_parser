import requests
import bs4
from dotenv import load_dotenv, find_dotenv

from models import postgre_db, NotCheckedHuman

load_dotenv(find_dotenv())


def make_request():
    response = requests.get("https://randomus.ru/name?type=1&sex=10&count=100")
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    result = soup.find(id="result_textarea")
    people = result.text.split("\n")
    postgre_db.connect()
    people_to_db = []
    #print(response.status_code)
    for human in people:
        last_name, name = human.split()
        try:
            NotCheckedHuman.get(NotCheckedHuman.lastname == last_name and NotCheckedHuman.name == name)
        except Exception as e:
            people_to_db.append({'name': name, 'lastname': last_name})

    if people_to_db:
        print(len(people_to_db))
        with postgre_db.atomic():
            NotCheckedHuman.insert_many(people_to_db).execute()
    postgre_db.close()

while True:
    make_request()

