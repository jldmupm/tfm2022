#!/bin/bash

trap cleanup EXIT

function cleanup {
    echo "Stoping CONTAINERS"
    
    cd local_runtime/
    docker-compose down
    cd ../
}


function start_containers {
    echo "Starting CONTAINERS"
    cd local_runtime/
    docker-compose up -d
    cd ../
}

function start_analysis_framework {
    echo "Starting Analysis Framework"
    poetry run ./run.sh
}

start_containers

start_analysis_framework
