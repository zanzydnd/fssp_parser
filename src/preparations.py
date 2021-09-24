from dotenv import load_dotenv, find_dotenv
from models import postgre_db, NotCheckedHuman, FSSPHuman, TaskCode, Statistic

load_dotenv(find_dotenv())


def preparations():
    with postgre_db:
        postgre_db.create_tables([NotCheckedHuman, FSSPHuman, TaskCode, Statistic])

preparations()