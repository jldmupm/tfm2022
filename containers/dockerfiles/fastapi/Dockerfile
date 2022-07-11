FROM python:3.8.13
MAINTAINER JLD <jl.domenech@alumnos.upm.es>

EXPOSE 80

ADD ./analysis /opt/app/analysis/
ADD ./pyproject.toml /opt/app/
ADD ./run-api.sh /opt/app/
ADD ./api /opt/app/api
ADD ./defaults.yml /opt/app/

RUN pip install poetry

WORKDIR /opt/app/

RUN mkdir -p /opt/app/keys/

RUN poetry install --no-dev

# USE environment variables:
# - SCHEDULER_TYPE (one of "distributed", "threads", "processes", "single-threaded")
# - SCHEDULER_URL (an URL to the scheduler)
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

ENV SCHEDULER_TYPE=distributed

CMD ["./run-api.sh"]
