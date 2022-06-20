import uvicorn

import analysis.config as cfg
import analysis.dashboard.dashboard as dashboard
import analysis.api.api as api

# TODO: use Tornado or Fastapi instead of Flask
if __name__ == '__main__':
    print('* * * MAIN * * *')
    flask_name = 'web ui'

    with cfg.get_dask_client() as dclient:
        print(dclient)

        uvicorn.run(app="analysis.api.api:api_app", host="localhost", port=9080, log_level="info", reload=True)
