import dask.distributed
import pandas as pd

import analysis.process.analyze as analyze_data

def get_service_distributed_data(client: dask.distributed.Client):
    print('GETTING service distributed data')
    return analyze_data.get_base_data(client)
