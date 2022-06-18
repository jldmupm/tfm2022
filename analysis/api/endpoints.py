import flask

from analysis.api.services import get_base_data

api_app = flask.Flask('api_app')

@api_app.get('/version')
def api_get_version():
    return

def setup_app(name: str, server: flask.Flask, url_base_pathname: str, dask_client):
    api_app.dask_client = dask_client
    get_base_data(dask_client)
    return api_app
