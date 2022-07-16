from dashboard.app import app

# ***********************
#    DASHBOARD MAIN
# ***********************
if __name__ == '__main__':
    app.run_server(debug=True)
    # gunicorn dashboard.server:app --workers 8
