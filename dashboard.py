from dask.distributed import Client

import analysis.dashboard.dashboard

if __name__ == '__main__':
    print('* * * DASHBOARD * * *')
    custom_dask_client = Client("127.0.0.1:8787")
    analysis.dashboard.dashboard.setup_layout(analysis.dashboard.dashboard.dash_app)
    analysis.dashboard.dashboard.dash_app.run(port="9080")

