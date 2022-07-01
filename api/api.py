import fastapi
from fastapi.responses import JSONResponse

import uvicorn

from api.endpoints import analysis_router

import analysis.config as cfg


api_app = fastapi.FastAPI(name='Sensor + CrowdSensing Analysis API',
                          version=cfg.get_version(),
                          redoc_url='/')

api_app.include_router(analysis_router, prefix='/api/v1')


@api_app.exception_handler(Exception)
async def handle_exception(request, exc):
    return JSONResponse(content={'error': 'internal', 'message': str(exc)}, status_code=500)


if __name__ == '__main__':
    uvicorn.run(app="api.api:api_app", host="localhost", port=9080, log_level="info", reload=True)
