

def test_doc(testapp):
    response = client.get("/")
    assert response.status_code == 200
    assert 'Sensor + CrowdSensing Analysis API' in response.text

