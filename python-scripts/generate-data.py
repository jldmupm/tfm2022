# -*- coding: utf-8 -*-
from pprint import pprint
import random
from typing import Optional
import datetime

import pytz

import analysis.feedback.fb_source as fs
import analysis.feedback.models as fbmodels
import analysis.sensors.mg_source as mg

from .vars import INIT_TIME, RANDOM_CLASSES

RANDOM_SUBJECT_IDS=["Inglés Nivel Avanzado", "Programación Concurrente y Avanzada", "Sistemas Distribuidos", "Sistemas Empotrados", "Sistemas de Tiempo Real", "Programación", "Aspectos Éticos y Sociales", "Fundamentos de Economía y Empresa", "Aspectos Legales y Profesionales", "Inteligencia Artificial", "Sistemas Basados en Computador", "Programación de Hardware Reconfigurable", "Seguridad de Sistemas y Redes"]

def random_vote(category = None):
    a_category: Optional[fbmodels.Category] = None
    if category:
        a_category = fbmodels.CategoriesEnum.get_by_category_id(category)
    else:
        a_category = random.choice(fbmodels.CategoriesEnum.all_categories())
    assert a_category, "A fail getting a random category"
    random_score = random.randrange(fbmodels.MIN_SCORE, fbmodels.MAX_SCORE + 1)
    if random_score > fbmodels.MID_SCORE:
        posible_values = a_category.positive_values
    elif random_score < fbmodels.MID_SCORE:
        posible_values = a_category.negative_values
    else:
        posible_values = a_category.negative_values + a_category.positive_values
    random_reasons_list = tuple([random.choice(posible_values) for _ in range(1, random.randrange(2, 3))])
    return fbmodels.Vote(
        category=a_category.name,
        reasonsList=random_reasons_list,
        reasonsString=", ".join(random_reasons_list),
        score=random_score
    )

def random_survey(category_tag = 'Ambiente',
                  date=datetime.datetime.now(pytz.timezone('Europe/Madrid')),
                  room=random.choice(RANDOM_CLASSES),
                  subject: str= random.choice(RANDOM_SUBJECT_IDS),
                  **kwargs):
    return fbmodels.Survey(
        date=date,
        duration=kwargs.get('duration', 2),
        room=room,
        subjectId=subject,
        votingTuple=tuple([random_vote(category.name) for category in fbmodels.CategoriesEnum.all_categories()]))

gen_temp_room = lambda prev = 20.0: ('room_temp', max(-20, prev + (random.randrange(-15, 15) / 10.0)))
gen_temp_add = lambda prev = 20.0: ('add_temp', max(-20, prev + (random.randrange(-15, 15) / 10.0)))
gen_temp_surf = lambda prev = 20.0: ('surf_temp', max(-20, prev + (random.randrange(-15, 15) / 10.0)))
gen_humidity = lambda prev = 10: ('humidity', max(0, prev + (random.randrange(-15, 15) / 10.0)))
gen_luminosity = lambda prev = 250: ('luminosity', max(0,prev + (random.randrange(-200, 200) / 100.0)))
gen_movimiento = lambda _ = False: ('movement', 1 if random.choice([False, True]) else 0)
gen_co2 = lambda prev = 10: ('co2', max(0, prev + (random.randrange(-10, 10) / 10.0)))
gen_noise = lambda prev = 0: ('noise', prev if random.randrange(0, 5) < 1 else 1 if prev == 0 else 0)

RANDOM_SET_OF_SENSORS = [
    [gen_luminosity, gen_humidity, gen_temp_room, gen_temp_surf, gen_temp_add, gen_co2],
    [gen_luminosity, gen_humidity, gen_temp_room, gen_temp_surf, gen_temp_add],
    [gen_humidity, gen_temp_room, gen_co2],
    [gen_noise],
]
RANDOM_HUB=["000FF001","000FF002","000FF003", "000FF004", "000FF005", "000FF006", "000FF07"]
RANDOM_NODE=["131333","131334","131335", "131336", "131337", "131338", "131339"]
RANDOM_CLASS_HUB_ID = ['a674c2b0-d1a7-4b12-9d51-aa280d360985', 'ad0bd1a7-420e-469c-aebe-8ffaeef36744', 'a20620ec-08a8-43a5-bcb3-9b11b5de4d20', '9327af92-c1f1-45ff-a2cb-24e09570e3c8', '3da08279-d303-4721-92fa-05c769cc8ba6', 'a0115824-a0c5-4a69-8de2-d01a56e909c3', 'dca3667b-d7ed-474f-bbf4-e305f6a069e9', '89979dff-0eb8-4eb1-b526-536daeef15fc', '83a96375-282b-4d81-b430-a9eeb43cb676', '5aef5840-bb1a-430c-9bb1-685af1e1e7ef', 'a67432b0-d1a7-4b12-9d51-bbb280d360985', 'a99c2b0-d1a7-4b12-9d51-aa280d367754', 'a674c2c1-d1a7-4b12-9d51-bc280d360932', 'af94c2b0-d0a7-4b11-8d51-ca280d270982']

def gen_random_sensor():
    return {
        'id': {
            'class': RANDOM_CLASSES[0],
            'hub': RANDOM_HUB[0],
            'node': RANDOM_NODE[0],
            'id': RANDOM_CLASS_HUB_ID[0]
        },
        'sensors': RANDOM_SET_OF_SENSORS[0]
    }

def random_motas_entries_in_period(mota_definition: dict,
                                   init_timestamp:float,
                                   inc_secs: int=60*15,
                                   max_timestamp: float=0,
                                   num_readings: int=4*2,
                                   num_errors: int = 1):
    n_error = 0
    n_entry = 0
    prev = [gen()[1] for gen in mota_definition['sensors']]
    ref_timestamp = init_timestamp
    while ref_timestamp < max_timestamp:
        ref_timestamp += inc_secs
        n_entry += 1
        new_pair_values = [pair_gen(prev[n_entry]) for n_entry, pair_gen in enumerate(mota_definition['sensors'])]
        new_values =  {k: v for (k, v) in new_pair_values}
        prev = [v for v in new_values.values()]

        if (n_error < num_errors) and (random.random() < 0.4):
            yield {
                'time': datetime.datetime.fromtimestamp(init_timestamp + (n_entry*inc_secs)),
                'data': {
                    'error': random.choice(['BR1750: Device is not configured!', b'\123\123a\0\56\47b\204\123c\10'])
                },
                **mota_definition['id']
            }
        else:
            yield {
                'time': datetime.datetime.fromtimestamp(init_timestamp + (n_entry*inc_secs)),
                'data': {
                    **new_values
                },
                **mota_definition['id']
            }
    for n_entry in range(num_readings, num_readings + (num_errors - n_error)):
        yield {
            'time': datetime.datetime.fromtimestamp(init_timestamp + (n_entry*inc_secs)),
            'data': {
                'error': random.choice(['BR1750: Device is not configured!', b'\123\123a\0\56\47b\204\123c\10'])
            },
            **mota_definition['id']
        }


def main():
    firebase_db = fs.get_firestore_db_client()
    mongo_collection = mg.get_mongodb_collection()

    num_readings = 0
    num_votes = 0
    timestamp = int(INIT_TIME)
    inc_secs = 60 * 15
    max_timestamp = timestamp + (30*24*60*60)
    mota = gen_random_sensor()
    for time in range(timestamp, max_timestamp, inc_secs * 4 * 2):
        print(datetime.datetime.fromtimestamp(time))
        vote: fbmodels.Survey = random_survey(date=datetime.datetime.fromtimestamp(time),room=mota['id']['class'])
        id_vote = str(hash(vote))
        doc_ref = firebase_db.collection(u'feedback').document(f'{id_vote}')
        doc_ref.set(vote.dict())
        num_votes += 1


    # for reading in random_motas_entries_in_period(mota, timestamp, inc_secs=inc_secs, max_timestamp=max_timestamp):
    #     print(reading['time'])
    #     mongo_collection.insert_one(reading) # TODO: insert_many
    #     num_readings += 1


    print(f"{num_readings=}, {num_votes=}")
if __name__ == '__main__':
    main()
