import os

import unittest.mock

import analysis.config as cfg

TEST_CONFIG = {
        "SCHEDULER_TYPE":"single-thread",
        "SCHEDULER_DISTRIBUTED_URL":"127.0.0.1:8786",
        "MONGO_HOST":"127.0.0.1",
        "MONGO_DATABASE":"sensor",
        "MONGO_PORT":"27017",
        "MONGO_COLLECTION":"readings",
        "MONGO_AUTH_MECHANISM":"&authSource=admin&authMechanism=SCRAM-SHA-1",
        "FIREBASE_COLLECTION":"feedback",
        "USE_FILE_INSTEAD_OF_FIRESTORE":"./all_feedbacks.csv",
        "MONGODB_SENSOR_USERNAME": "BLUE",
        "MONGODB_SENSOR_PASSWORD": "RED",
        "FIREBASE_FEEDBACK_KEYPATH": "/path/to/key.json"
}

def test_internal_get_env_credentials():
    with unittest.mock.patch.dict(os.environ, TEST_CONFIG):
        res = cfg._get_env_credentials()
        assert all(list(map(lambda k: k in res.keys(), ['mongodb', 'firebase'])))
        assert all(list(map(lambda k: k in res['mongodb'].keys(), ['username', 'password'])))
        assert res['mongodb']['username'] == 'BLUE'
        assert res['mongodb']['password'] == 'RED'
        assert all(list(map(lambda k: k in res['firebase'].keys(), ['keypath'])))
        assert res['firebase']['keypath'] == "/path/to/key.json"

def test_get_mongo_credentials():
    with unittest.mock.patch.dict(os.environ, TEST_CONFIG):
        res = cfg.get_mongodb_connection_string()
        assert isinstance(res, str)
        assert len(res) > 0
        assert "BLUE" in res
        assert "RED" in res

def test_get_firebase_credentials():
    with unittest.mock.patch.dict(os.environ, TEST_CONFIG):
        res = cfg.get_firebase_file_credentials()
        assert isinstance(res, str)
        assert len(res) > 0
        assert res == "/path/to/key.json"
