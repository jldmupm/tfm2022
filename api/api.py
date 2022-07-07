import fastapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import uvicorn

import analysis.config as cfg

from api.endpoints import analysis_router
import analysis.cluster as cluster

api_app = fastapi.FastAPI(name='Sensor + CrowdSensing Analysis API',
                          version=cfg.get_version(),
                          docs_url='/test',
                          redoc_url='/')

api_app.include_router(analysis_router, prefix='/api/v1', dependencies=[fastapi.Depends(cluster.get_dask_client)])


@api_app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request, exc):
    return JSONResponse(content={'error': 'request', 'message': str(exc)}, status_code=400)

@api_app.exception_handler(Exception)
async def handle_exception(request, exc):
    return JSONResponse(content={'error': 'internal', 'message': str(exc)}, status_code=500)


if __name__ == '__main__':
    api_conf = cfg.get_config().api
    uvicorn.run(app="api.api:api_app", host=api_conf.get('host','localhost'), port=int(api_conf.get('port', '9080')), log_level="info", reload=True)
