from dask.distributed import Client, Worker, WorkerPlugin
from dask.distributed import PipInstall as PipInstallPlugin
import dask.config
import dask.bag
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import flask

import pymongo

import analysis.config as cfg
import analysis.dashboard.dashboard as dashboard
import analysis.api.endpoints as api

class WorkerDatasourcePlugin(WorkerPlugin):
    def __init__(self, mongodb_url: str, sensor_database: str, sensor_collection: str):
        self.mongodb_url = mongodb_url
        self.sensor_database = sensor_database
        self.sensor_collection = sensor_collection

    def setup(self, worker: Worker):
        print('hello', worker)
        sensor_db = pymongo.MongoClient(self.mongodb_url)
        worker.sensor_db = sensor_db
        worker.sensor_db_collection = sensor_db[self.sensor_database][self.sensor_collection]

    def teardown(self, worker: Worker):
        print("goodbye", worker)
        worker.sensor_db.close()

# TODO: use Tornado or Fastapi instead of Flask
if __name__ == '__main__':
    print('* * * MAIN * * *')
    flask_name = 'web ui'
    custom_client = None
    dask.config.set(scheduler=cfg.get_scheduler_preconfig()) # threads, processes, synchronous
    if cfg.get_scheduler_preconfig() in ['distributed']:
        # distributed. The scheduler.
        url_scheduler = cfg.get_scheduler_url()
        custom_client = Client(url_scheduler, name='tfm2022_distributed')
    else:
        custom_client = Client(name='tfm2022_non_distributed')
    url_string = cfg.get_mongodb_connection_string()
    sensor_database = cfg.get_config().datasources.sensors.database
    sensor_collection = cfg.get_config().datasources.sensors.collection
    dependencies_plugin = PipInstallPlugin(packages=["pymongo"], pip_options=["--upgrade"])
    worker_db_plugin = WorkerDatasourcePlugin(url_string, sensor_database, sensor_collection)
    custom_client.register_worker_plugin(dependencies_plugin)
    custom_client.register_worker_plugin(worker_db_plugin)

    print(custom_client)
    with custom_client as client:
        server: flask.Flask = flask.Flask(flask_name)
        api_flask_app = api.setup_app(name=f"{flask_name}_api", dask_client=client)
        dashboard_flask_app = dashboard.create_dash_app(dask_client=client)

        server = DispatcherMiddleware(dashboard_flask_app.wsgi_app, {
            '/api/v1': api_flask_app,
        })
        
        # TODO: use gunicorn
        # TODO: use asynchronous server calls & uvicorn ?
        run_simple('localhost', 5000, server, use_reloader=True, use_debugger=True, use_evalex=True)
