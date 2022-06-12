import os
import typing

import pytest

import analysis.config as cfg

@pytest.fixture
def mocked_environment_credentials(mocker):
    mocker.patch.dict(os.environ, {"MONGODB_SENSOR_USERNAME": "BLUE", "MONGODB_SENSOR_PASSWORD": "RED", "FIREBASE_FEEDBACK_KEYPATH": "/path/to/key.json"})


def test_internal_get_env_credentials(mocked_environment_credentials):
    res = cfg._get_env_credentials()
    assert all(list(map(lambda k: k in res.keys(), ['mongodb', 'firebase'])))
    assert all(list(map(lambda k: k in res['mongodb'].keys(), ['username', 'password'])))
    assert res['mongodb']['username'] == 'BLUE'
    assert res['mongodb']['password'] == 'RED'
    assert all(list(map(lambda k: k in res['firebase'].keys(), ['keypath'])))
    assert res['firebase']['keypath'] == "/path/to/key.json"

def test_get_mongo_credentials(mocked_environment_credentials):
    res = cfg.get_mongodb_connection_string()
    assert isinstance(res, str)
    assert len(res) > 0
    assert "BLUE" in res
    assert "RED" in res

def test_get_firebase_credentials(mocked_environment_credentials):
    res = cfg.get_firebase_file_credentials()
    assert isinstance(res, str)
    assert len(res) > 0
    assert res == "/path/to/key.json"

def test_get_scheduler_preconfig():
    res = cfg.get_scheduler_preconfig()
    assert isinstance(res, str)
    assert res in typing.get_args(cfg.DaskClusterType)
    
def test_get_scheduler_url():
    res = cfg.get_scheduler_url()
    assert isinstance(res, str)
    assert len(res) > 0

