import os
import unittest.mock
from pymongo.common import LOCAL_THRESHOLD_MS

import pytest
import dateparser

import analysis.config as cfg
import analysis.sensors.mg_source as mg

LOCAL_MONGO_SERVER_CONFIG = {
    "SCHEDULER_TYPE":"single-thread",
    "SCHEDULER_DISTRIBUTED_URL":"127.0.0.1:8786",
    "MONGO_HOST":"127.0.0.1",
    "MONGO_DATABASE":"sensor",
    "MONGO_PORT":"27017",
    "MONGO_COLLECTION":"readings",
    "MONGO_AUTH_MECHANISM":"&authSource=admin&authMechanism=SCRAM-SHA-1",
    "FIREBASE_COLLECTION":"feedback",
    "USE_FILE_INSTEAD_OF_FIRESTORE":"./all_feedbacks.csv",
    "MONGODB_SENSOR_USERNAME": "sensorUser",
    "MONGODB_SENSOR_PASSWORD": "password"
}

TEST_EXAMPLE_INSERTED = {
    'time': dateparser.parse('2022-06-09T22:00:00.000Z'),
    'data': {
        'noise': 0
    },
    'class': '1001',
    'hub': '000FF003',
    'node': '131334',
    'id': 'TEST_EXAMPLE_INSERTED'
}

TEST_EXAMPLE_DURATION = 2

@pytest.fixture
def setup_mongodb_collection(mocker):
    with unittest.mock.patch.dict(os.environ, LOCAL_MONGO_SERVER_CONFIG):
        # setup
        print('******TESTS SETUP******')

        cfg.get_config(force=True)
        
        mongodb_sensor_collection = mg.get_mongodb_collection()
        res = mongodb_sensor_collection.insert_one(TEST_EXAMPLE_INSERTED)

        yield mongodb_sensor_collection

        # teardown
        print('******TEST TEARDOWN******')
        mongodb_sensor_collection.delete_many({ 'id': TEST_EXAMPLE_INSERTED['id'] })


def test_average_sensor_data(setup_mongodb_collection):
    res = mg.get_average_sensor_data(
        setup_mongodb_collection,
        TEST_EXAMPLE_INSERTED['time'],
        TEST_EXAMPLE_DURATION,
        TEST_EXAMPLE_INSERTED['class'],
        'group_kind_sensor')
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0].get('r_avg', None), (float, int))
