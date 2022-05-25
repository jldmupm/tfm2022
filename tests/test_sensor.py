from dateutil import parser
from src.sensors.mg_source import flatten_sensor_dict

ObjectId = str
ISODate = parser.parse

SENSOR_TO_TEST = {
    "_id": ObjectId('629a4e5cfcb664f8cb3a2193'),
    "time": ISODate('2022-05-12T22:46:00.000Z'),
    "data": {
        "luminosity": 54,
        "humidity": 150.8,
        "room_temp": 19.60000000000001,
        "surf_temp": 13.899999999999995,
        "add_temp": 15.100000000000001
    },
    "class": 'CIC-4',
    "hub": '000FF001',
    "node": 'a674c2b0-d1a7-4b12-9d51-aa280d360985'
}

def test_flatten_sensor_dict():
    flatten = flatten_sensor_dict(SENSOR_TO_TEST)

    assert len(flatten) == len(SENSOR_TO_TEST['data'])
    assert all(list(map(lambda e: e.get('sensor') in SENSOR_TO_TEST['data'].keys(), flatten)))
