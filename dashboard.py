from dask.distributed import Client
from distributed.deploy.local import LocalCluster

import analysis.config as cfg

import analysis.dashboard.dashboard

if __name__ == '__main__':
    print('* * * DASHBOARD * * *')
    if cfg.get_config().cluster.scheduler in ['distributed']:
        print('configured as distributed cluster')
        custom_dask_client = Client(cfg.get_config().cluster.distributed)
    else:
        print('configured as local cluster')
        custom_dask_client = Client(LocalCluster("127.0.0.1:8787", dashboard_address="0.0.0.0:8687"))
        custom_dask_client.cluster.scale(cfg.get_config().cluster.workers)
    print(custom_dask_client)
    cfg.set_cluster_client(custom_dask_client)

    analysis.dashboard.dashboard.setup_layout(analysis.dashboard.dashboard.dash_app)
    analysis.dashboard.dashboard.dash_app.run(port="9081")

