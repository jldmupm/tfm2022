#!/bin/bash

trap cleanup EXIT

function cleanup {
    echo "Stoping CONTAINERS"
    docker-compose down
    cd ../
}


function start_containers {
    echo "Starting CONTAINERS"
    docker-compose up -d
}

start_containers
read -p "Press any key to shutdown the services... " -n 1 -r

