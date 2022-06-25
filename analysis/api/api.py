import fastapi
from fastapi.responses import JSONResponse

from analysis.api.endpoints import analysis_router

import analysis.config as cfg

api_app = fastapi.FastAPI(name='Sensor + CrowdSensing Analysis API', version=cfg.get_version())

api_app.include_router(analysis_router)

@api_app.exception_handler(Exception)
def handle_exception(request, exc):
    return JSONResponse(content={'error': 'internal'}, status_code=500)
