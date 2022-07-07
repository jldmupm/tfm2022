import dask.distributed

import analysis.config as cfg

async def get_dask_client():
    client: dask.distributed.Client = dask.distributed.Client(address=cfg.get_cluster())
    yield client
    #client.close()
