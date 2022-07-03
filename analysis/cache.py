from pymongo import MongoClient

import analysis.config as cfg

def cache_app_mongetter():
    cache_conf = cfg.get_config().cache
    client = MongoClient(cfg.get_mongodb_cache_connection_string())
    db_obj = client[cache_conf.database]
    if cache_conf.collection not in db_obj.list_collection_names():
        db_obj.create_collection(cache_conf.collection)
    return db_obj[cache_conf.collection]

# usage:
# @cachier(mongetter=cache_app_mongetter)
