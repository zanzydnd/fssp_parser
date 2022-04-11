# entry.891491422: Ваш возраст / пол / должность?
# entry.1231258737: Разных
# entry.2044583059: 123123
# entry.1211791576: Да
# entry.1331768927: Нет
# entry.803973658: не знаю
# entry.136654540: рекомендовал(а) бы
# entry.1507176324: Восстановитель памяти
# entry.1429166132: Скорее нет, чем да
# entry.1969921016: Да
import time
import random

import requests

URL = "https://docs.google.com/forms/d/e/1FAIpQLSdiCkSKeuXnqpms0lkZYq4cINCcDJ_f8_Y0Z6xWu04pcuZeAQ"

urlResponse = URL + '/formResponse'
urlReferer = URL + '/viewform'

sex = ['Мусжкой,Женский']

position = ['Заведующий', 'Уборщик', 'Студент', 'Преподаватель', 'Менеджер', 'Владелец']

yes_no = ["Да", "Нет"]
yes_no_small = ["да", "нет"]

_ = ["Восстановитель памяти", "Стиратель памяти", "Обе"]

__ = ["Да", "Скорее да, чем нет", "Скорее нет, чем да", "Нет"]

___ = ["скорее нет, чем да", "не рекомендовал(а) бы", "скорее да, чем нет", "рекомендовал(а) бы"]

____ = ["скорее да, чем нет", "скорее нет, чем да", "да", "нет", "не знаю"]

long_answer = ["Для разных", "Стирать память", "Лечить людей", "Психология", "Военные действия", "Никак"]


def generate_form_data() -> dict:
    return {
        "entry.891491422": str(random.randint(19, 60))+ " " + random.choice(sex)+ " " + random.choice(position),
        "entry.1231258737": random.choice(long_answer),
        "entry.2044583059": str(random.randint(1000, 1_000_000_000)),
        "entry.803973658": random.choice(____),
        "entry.136654540": random.choice(___),
        "entry.1211791576": random.choice(yes_no),
        "entry.1331768927": random.choice(yes_no),
        "entry.1969921016": random.choice(yes_no),
        "entry.1429166132": random.choice(__),
        "entry.1507176324": random.choice(_)
    }


if __name__ == '__main__':
    i = 0
    while i < 40:
        form_data = generate_form_data()
        user_agent = {'Referer': urlReferer,
                      'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36"}

        r = requests.post(urlResponse, data=form_data, headers=user_agent)

        print("done")
        #time.sleep(5)
        i += 1
