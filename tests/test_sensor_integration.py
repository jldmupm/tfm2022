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
def mongodb_collection():
    # setup
    print('******SETUP******')
    mongodb_sensor_collection = mg.get_mongodb_collection()
    res = mongodb_sensor_collection.insert_one(TEST_EXAMPLE_INSERTED)

    yield mongodb_sensor_collection

    # teardown
    print('******TEARDOWN******')
    mongodb_sensor_collection.delete_many({ 'id': TEST_EXAMPLE_INSERTED['id'] })


def test_average_sensor_data(mongodb_collection):
    res = mg.get_average_sensor_data(
        mongodb_collection,
        TEST_EXAMPLE_INSERTED['time'],
        TEST_EXAMPLE_DURATION,
        TEST_EXAMPLE_INSERTED['class'],
        'group_kind_sensor')
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0].get('avg', None), (float, int))
