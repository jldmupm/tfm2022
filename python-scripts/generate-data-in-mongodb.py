import random
import datetime
from pprint import pprint

from src.config import config as cfg
import src.sensors.mg_source as mg

gen_temp_room = lambda prev = 20.0: ('room_temp', prev + random.randrange(-15, 15) / 10.0)
gen_temp_add = lambda prev = 20.0: ('add_temp', prev + random.randrange(-15, 15) / 10.0)
gen_temp_surf = lambda prev = 20.0: ('surf_temp', prev + random.randrange(-15, 15) / 10.0)
gen_humidity = lambda prev = 10: ('humidity', prev + random.randrange(-15, 15) / 10.0)
gen_luminosity = lambda prev = 250: ('luminosity', prev + random.randrange(-200, 200) / 100.0)
gen_movimiento = lambda prev = False: ('movement', 1 if random.choice([False, True]) else 0)
gen_co2 = lambda prev = 10: ('co2', max(0, prev + random.randrange(-10, 10) / 10.0))
gen_noise = lambda prev = 0: ('noise', prev if random.randrange(0, 5) < 1 else 1 if prev == 0 else 0)

RANDOM_CLASSES=["3203", "CIC-4", "3104", "1001", "CIC-3", "3301", "3302"]

RANDOM_SET_OF_SENSORS = [
    [gen_luminosity, gen_humidity, gen_temp_room, gen_temp_surf, gen_temp_add],
    [gen_humidity, gen_temp_room, gen_co2],
    [gen_noise],
]
RANDOM_HUB=["000FF001","000FF002","000FF003"]
RANDOM_NODE=["131333","131334","131335"]
RANDOM_CLASS_HUB_ID = [(1, 0, 'a674c2b0-d1a7-4b12-9d51-aa280d360985'), (1, 0, 'ad0bd1a7-420e-469c-aebe-8ffaeef36744'), (2, 1, 'a20620ec-08a8-43a5-bcb3-9b11b5de4d20'), (2, 1, '9327af92-c1f1-45ff-a2cb-24e09570e3c8'), (2, 1, '3da08279-d303-4721-92fa-05c769cc8ba6'), (2, 1, 'a0115824-a0c5-4a69-8de2-d01a56e909c3'), (2, 2, 'dca3667b-d7ed-474f-bbf4-e305f6a069e9'), (2, 2, '89979dff-0eb8-4eb1-b526-536daeef15fc'), (2, 2, '83a96375-282b-4d81-b430-a9eeb43cb676'), (2, 2, '5aef5840-bb1a-430c-9bb1-685af1e1e7ef')]

def random_mota_entry(kind_of_sensor=1, init_time=1652370360, inc_secs=60*15, num_entries=45):
    i = 0
    sensor_type = RANDOM_CLASS_HUB_ID[kind_of_sensor]
    t_hub = sensor_type[1]
    sensor_type_sensors = RANDOM_SET_OF_SENSORS[t_hub]
    prev = [gen()[1] for gen in sensor_type_sensors]
    while i < num_entries:
        new_pair_values = [pair_gen(prev[i]) for i, pair_gen in enumerate(sensor_type_sensors)]
        new_values =  {k: v for (k, v) in new_pair_values}
        prev = [v for v in new_values.values()]
        yield {
            'time': datetime.datetime.fromtimestamp(init_time + (i*inc_secs)),
            'data': {
                **new_values
            },
            'class': RANDOM_CLASSES[sensor_type[0]],
            'hub': RANDOM_HUB[t_hub],
            'node': RANDOM_CLASS_HUB_ID[t_hub][2],
        }
        i += 1

if __name__ == '__main__':
    collection = mg.get_mongodb_database(cfg.datasources.sensors)[cfg.datasources.sensors['collection']]
    for mota in [random.randrange(0, len(RANDOM_CLASS_HUB_ID)-1) for _ in range(30)]:
        for value in random_mota_entry(kind_of_sensor=mota, init_time=datetime.datetime(2022,6,9,22,0).timestamp(), num_entries=200, inc_secs=60*random.randrange(15, 33)):
            pprint(value)
            collection.insert_one(value)
