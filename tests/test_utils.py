import src.utils.utils as utils

MONGODB_TEST = {
        "type": "sensor",
        "host": "localhost",
        "database": "sensor",
        "collection": "readings",
        "credentials": {
            "username": "testuser",
            "password": "testpassword",
            "auth_mechanism": ""
        },
    }

def test_get_mongo_credentials():
    res = utils.get_mongodb_connection_string(MONGODB_TEST)
    assert isinstance(res, str)
    assert len(res) > 0
    assert MONGODB_TEST['host'] in res
