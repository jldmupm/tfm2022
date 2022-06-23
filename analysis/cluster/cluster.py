# TODO: prepare a custom Docker image with pymongo already installed
class WorkerDatasourcePlugin(WorkerPlugin):
    def __init__(self, mongodb_url: str, sensor_database: str, sensor_collection: str, credentials_json):
        self.mongodb_url = mongodb_url
        self.sensor_database = sensor_database
        self.sensor_collection = sensor_collection
        self.credentials = credentials_json
        
    def setup(self, worker: Worker):
        print('hello', worker)
        sensor_db = pymongo.MongoClient(self.mongodb_url)
        worker.sensor_db = sensor_db
        worker.sensor_db_collection = sensor_db[self.sensor_database][self.sensor_collection]

        cred_filename = 'f{worker.local_directory}/worker_credentials_{worker.name}.json'
        with open(cred_filename, 'wb') as fout:
            fout.write(self.credentials)

        cred_obj = firebase_admin.credentials.Certificate(cred_filename)
        default_app = firebase_admin.initialize_app(credential=cred_obj)
        firestore_db = firestore.client()
        worker.feedback_db = firestore_db
        
    def teardown(self, worker: Worker):
        print("goodbye", worker)
        worker.sensor_db.close()


if __name__ == '__main__':
    print('* * * DASK * * *')
    print(f'Setting Dask Configuration as {cfg.get_config().cluster.scheduler}')
    #    dask.config.set(scheduler=cfg.get_config().cluster.scheduler)
    if cfg.get_config().cluster.scheduler in ['distributed']:
        print(f'Setting Future Dask Workers')
        custom_dask_client = Client(cfg.get_config().cluster.distributed)
        print(1)
        url_string = cfg.get_mongodb_connection_string()
        print(2)
        sensor_database = cfg.get_config().datasources.sensors.database
        print(3)
        sensor_collection = cfg.get_config().datasources.sensors.collection
        print(4)
        dependencies_plugin = PipInstallWorkerPlugin(packages=["pymongo", "firebase-admin"], pip_options=["--upgrade"])
        print(5)
        worker_db_plugin = WorkerDatasourcePlugin(url_string, sensor_database, sensor_collection)
        print(6)
        custom_dask_client.register_worker_plugin(dependencies_plugin)
        print(7)
        custom_dask_client.register_worker_plugin(worker_db_plugin)    
        print(8)
    else:
        custom_dask_client = Client(LocalCluster())
