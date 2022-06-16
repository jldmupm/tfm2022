from pprint import pprint

from src.config import config as cfg
import src.sensors.mg_source as mg

if __name__ == '__main__':
    cursor = mg.get_mongodb_database(cfg.datasources.sensors)[cfg.datasources.sensors['collection']].find()
    for d in cursor:
        pprint(d)
