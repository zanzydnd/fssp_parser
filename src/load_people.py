import os
import sys

from dotenv import load_dotenv, find_dotenv
from models import postgre_db, NotCheckedHuman
from openpyxl import load_workbook

load_dotenv(find_dotenv())


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
            NotCheckedHuman.get(NotCheckedHuman.lastname == map['lastname'] and NotCheckedHuman.name == map['name'])
            duplicate_people.append(map)
        except Exception as e:
            people.append(map)
        i += 1

    if duplicate_people:
        f = open(os.path.join(os.path.abspath(os.path.curdir), "statistics", "duplicates", filename[:-4] + "txt"), "w",
                 encoding="utf-8")
        f.write(str(duplicate_people))
        f.write("\n")
        f.write("Кол-во дупликатов: " + str(len(duplicate_people)))
        f.close()

    with postgre_db.atomic():
        NotCheckedHuman.insert_many(people).execute()

get_humans_from_excel(sys.argv[1])