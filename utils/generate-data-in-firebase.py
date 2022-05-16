# -*- coding: utf-8 -*-
import random
from typing import Optional
import datetime

import pytz
import dateparser

import src.feedback.fs_source as fs
import src.feedback.models as models


def random_vote(category = None, category_tag: str = 'name'):
    a_category: Optional[models.Category] = models.CategoriesEnum.get_by_category_id(category) if category else random.choice(models.CategoriesEnum.all_categories())
    assert a_category, "A fail getting a random category"
    random_score = random.randrange(models.MIN_SCORE, models.MAX_SCORE + 1)
    if random_score > models.MID_SCORE:
        posible_values = a_category.positive_values
    elif random_score < models.MID_SCORE:
        posible_values = a_category.negative_values
    else:
        posible_values = a_category.negative_values + a_category.positive_values
    random_reasons_list = tuple([random.choice(posible_values) for _ in range(1, random.randrange(2, 3))])
    return models.Vote(
        category=a_category.name if category_tag == 'name' else a_category.statement,
        reasonsList=random_reasons_list,
        reasonsString=", ".join(random_reasons_list),
        score=random_score
    )

def random_survey(category_tag = 'statment', **kwargs):
    return models.Survey(
        date=kwargs.get('date', datetime.datetime.now(pytz.timezone('Europe/Madrid'))),
        duration=kwargs.get('duration', 2),
        room=kwargs.get('room', random.choice(["3203", "CIC-4", "3104", "1001", "CIC-3", "3301", "3302"])),
        subjectId=kwargs.get('subjectId', random.choice(["Inglés Nivel Avanzado", "Programación Concurrente y Avanzada", "Sistemas Distribuidos", "Sistemas Empotrados", "Sistemas de Tiempo Real", "Programación", "Aspectos Éticos y Sociales", "Fundamentos de Economía y Empresa", "Aspectos Legales y Profesionales", "Inteligencia Artificial", "Sistemas Basados en Computador", "Programación de Hardware Reconfigurable", "Seguridad de Sistemas y Redes"])),
        votingTuple=tuple([random_vote(category.name, category_tag=category_tag) for category in models.CategoriesEnum.all_categories()]))

def main():
    firebase_db = fs.get_firestore_db()

    for d in range(130):
        days_ago = random.randrange(0, 20)
        survey_datetime = dateparser.parse(f'{days_ago} days ago')
        for v in range(random.randrange(1, 45)):
            print(f'  v={v}')
            feed: models.Survey = random_survey(date=survey_datetime)
            id_feed = str(hash(feed))
            doc_ref = firebase_db.collection(u'feedback').document(f'{id_feed}')
            print(feed.dict())
            doc_ref.set(feed.dict())


if __name__ == '__main__':
    main()
