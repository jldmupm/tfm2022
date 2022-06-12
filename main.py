from dask.distributed import Client, Worker, WorkerPlugin
import dask.config
import dask.bag
import flask

import pymongo

import analysis.config as cfg
import analysis.dashboard.dashboard

class WorkerDatasourcePlugin(WorkerPlugin):
    def __init__(self, mongodb_url: str, sensor_collection: str):
        self.mongodb_url = mongodb_url
        self.sensor_collection = sensor_collection

    def setup(self, worker: Worker):
        print('hello', worker)
        worker.sensor_db = pymongo.MongoClient(self.mongodb_url)
        worker.readings_collection = worker.sensor_db[self.sensor_collection]

    def teardown(self, worker: Worker):
        print("goodbye", worker)
        worker.sensor_db.close()

if __name__ == '__main__':
    custom_client = None
    dask.config.set(scheduler=cfg.get_scheduler_preconfig()) # threads, processes, synchronous
    if cfg.get_scheduler_preconfig() in ['distributed']:
        # distributed. The scheduler.
        url_scheduler = cfg.get_scheduler_url()
        custom_client = Client(url_scheduler, name='tfm2022_distributed')
    else:
        custom_client = Client(name='tfm2022_non_distributed')
    url_string = cfg.get_mongodb_connection_string()
    sensor_collection = cfg.get_config().datasources.sensors.collection
    worker_db_plugin = WorkerDatasourcePlugin(url_string, sensor_collection)
    custom_client.register_worker_plugin(worker_db_plugin)

    print(custom_client)
    with custom_client as client:
        d = dask.bag.from_sequence([1,2,3])
        print(d)
        c = d.compute()
        print(f'''

        RESULTADO: {c}

        ''')
        server: flask.Flask = flask.Flask(__name__)
        dashboard_flask_app = analysis.dashboard.dashboard.setup_app(name=__name__, server=server, url_base_pathname='/dashboard/', dask_client=client)
        # TODO: use gunicorn
        # TODO: use asynchronous server calls & uvicorn ?
        server.run(debug=True)
