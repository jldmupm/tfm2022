import datetime
from pprint import pprint

import pytest
import pymongo
import dateparser

import analysis.config as cfg
import analysis.sensors.mg_source as mg

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

@pytest.fixture(scope='module')
def mongoclient():
    # setup
    print('******SETUP******')
    mongocli = mg.get_mongodb_database(cfg.get_config())
    mongocli_readings = mongocli[cfg.get_config().datasources.sensors.collection]

    mongocli_readings.insert_one(TEST_EXAMPLE_INSERTED)

    yield mongocli

    # teardown
    print('******TEARDOWN******')
    mongocli_readings.delete_many({ 'id': TEST_EXAMPLE_INSERTED['id'] })


def test_average_sensor_data(mongoclient):
    res = mg.get_average_sensor_data(
        mongoclient,
        TEST_EXAMPLE_INSERTED['time'],
        TEST_EXAMPLE_DURATION,
        TEST_EXAMPLE_INSERTED['class'],
        'group_kind_sensor')
    assert isinstance(res, list)
    assert len(res) > 0
    assert res[0].get('avg', False)
