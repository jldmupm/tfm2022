import flask

from analysis.api.services import get_service_distributed_data

api_app = flask.Flask('api')

@api_app.route('/version', methods=['GET'])
def api_get_version():
    return "Hello!"

def setup_app(name: str, dask_client):
    api_app.dask_client = dask_client
    get_service_distributed_data(dask_client)
    
    return api_app
