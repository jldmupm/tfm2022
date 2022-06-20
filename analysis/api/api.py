import fastapi

from analysis.api.endpoints import analysis_router

api_app = fastapi.FastAPI()

api_app.include_router(analysis_router)

