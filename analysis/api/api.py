import fastapi

from analysis.api.endpoints import analysis_router

import analysis.config as cfg

api_app = fastapi.FastAPI(name='Sensor + CrowdSensing Analysis API', version=cfg.get_version())

api_app.include_router(analysis_router)

