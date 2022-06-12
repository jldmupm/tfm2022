import random
import datetime
from pprint import pprint

import analysis.config as cfg
import analysis.sensors.mg_source as mg

from .vars import INIT_TIME, RANDOM_CLASSES
NUM_READINGS_EACH_NODE=450


if __name__ == '__main__':
    collection = mg.get_mongodb_database(cfg.get_config())[cfg.get_config().datasources.sensors.collection]
    for reading in random_motas_entries(readings_each_sensor=NUM_READINGS_EACH_NODE):
        pprint(reading)
        collection.insert_one(reading)
