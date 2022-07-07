import dask.distributed

import analysis.config as cfg

client: dask.distributed.Client = dask.distributed.Client(address=cfg.get_cluster())

async def get_dask_client():
    global client
    yield client
    #client.close()
