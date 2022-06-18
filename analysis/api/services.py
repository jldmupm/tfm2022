import dask.distributed
import pandas as pd

import analysis.process.analyze as analyze_data

def get_min_date():
    return max(analyze_data.get_min_from_firebase('date'), analyze_data.get_min_from_mongo('date'))

def get_max_date():
    return min(analyze_data.get_max_from_firebase('date'), analyze_data.get_max_from_mongo('date'))

def get_service_distributed_data(client: dask.distributed.Client, **kwargs):
    print('GETTING service distributed data', kwargs)
    return analyze_data.get_base_data(client, **kwargs)
