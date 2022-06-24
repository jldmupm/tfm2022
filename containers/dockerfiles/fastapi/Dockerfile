FROM python:3.8.13

ADD ./analysis /opt/app/analysis/
ADD ./main.py /opt/app/
ADD ./pyproject.toml /opt/app/
ADD ./run-fastapi.sh /opt/app/

RUN pip install poetry

WORKDIR /opt/app/

RUN mkdir -p /opt/app/keys/

RUN poetry install --no-dev

# USE environment variables:
# - SCHEDULER_TYPE (one of "distributed", "threads", "processes", "single-threaded")
# - SCHEDULER_DISTRIBUTED_URL (an URL to the scheduler)
#
# - MONGODB_SENSOR_USERNAME
# - MONGODB_SENSOR_PASSWORD
# - FIREBASE_FEEDBACK_KEYPATH
#
# - MONGO_HOST
# - MONGO_DATABASE
# - MONGO_PORT
# - MONGO_COLLECTION
# - FIREBASE_COLLECTION
CMD ["./run-fastapi.sh"]

EXPOSE 80
