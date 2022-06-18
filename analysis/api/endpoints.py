import flask

from analysis.api.services import get_service_distributed_data

api_app = flask.Flask('api')

@api_app.route('/version', methods=['GET'])
def api_get_version():
    return flask.jsonify({
        'major': 0,
        'middle': 1,
        'minor': 0
    })

@api_app.route('/analyze', methods=['GET'])
def api_get_analysis():
    v = get_service_distributed_data(api_app.dask_client)
    return v['']head(2)

def setup_app(name: str, dask_client):
    api_app.dask_client = dask_client
    
    return api_app
