from dask.distributed import Client

import src.process.merging as merge

import src.config as cfg

def setup():
    client = Client(cfg.config['dask']['scheduler_url'])
    client.register_worker_callbacks(merge.worker_setup)
    return client
