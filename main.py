import uvicorn

import analysis.dashboard.dashboard as dashboard


if __name__ == '__main__':
    print('* * * DASHBOARD * * *')

#    uvicorn.run(app="analysis.api.api:api_app", host="localhost", port=9080, log_level="info", reload=True)

    dashboard.setup_layout(dashboard.dash_app)
    dashboard.dash_app.run(port="9080")
