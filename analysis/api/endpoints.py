import flask

from analysis.api.services import get_min_date, get_max_date

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
    pass

def setup_app(name: str, dask_client):
    api_app.dask_client = dask_client
    
    return api_app
