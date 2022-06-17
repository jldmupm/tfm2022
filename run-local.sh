#!/bin/sh

echo "Starting CONTAINERS"
cd local_runtime/
docker-compose up -d
cd ../

sleep 10

echo "Starting Analysis Framework"
poetry run ./run.sh

cd local_runtime/
docker-compose down
cd ../
