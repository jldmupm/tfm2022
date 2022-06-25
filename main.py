from dask.distributed import Client
from distributed.deploy.local import LocalCluster

import uvicorn

import analysis.config as cfg

# Dask Plugins

if __name__ == '__main__':
    print('* * * API * * *')
    if cfg.get_config().cluster.scheduler in ['distributed']:
        print('configured as distributed cluster')
        custom_dask_client = Client(cfg.get_config().cluster.distributed)
    else:
        print('configured as local cluster')
        custom_dask_client = Client(LocalCluster("127.0.0.1:8787", dashboard_address="0.0.0.0:8687"))
        custom_dask_client.cluster.scale(cfg.get_config().cluster.workers)
    print(custom_dask_client)
    cfg.set_cluster_client(custom_dask_client)

    uvicorn.run(app="analysis.api.api:api_app", host="localhost", port=9080, log_level="info", reload=True)
