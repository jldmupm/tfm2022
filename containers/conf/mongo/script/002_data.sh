#!/bin/bash

echo "########### Loading data to Mongo DB ###########"
mongoimport --jsonArray --db sensor --collection readings --file /tmp/data/data.json
