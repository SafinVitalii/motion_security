from random import randint

import pytest
import requests


class TestAPI(object):
    @pytest.mark.positive
    def test_login(self, api_client):
        resp = api_client.post('login/', data=api_client.auth)
        assert resp.status_code == requests.codes.ok, \
            "Failed to login: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    @pytest.mark.parametrize('credentials', [
        {'email': 'testt@gmail.com', 'password': 'Passw0rd#', "_id": "invalid_user"},
        {'email': 'test@gmail.com', 'password': 'Pass', "_id": "invalid_password"},
        {'email': 'test@gmail.com', "_id": "email_only"},
        {'password': 'Passw0rd#', "_id": "password_only"},
        {"_id": "empty"},
        {'email': ['test@gmail.com'], 'password': 'Passw0rd#', "_id": "email_is_not_string"},
        {'email': 'test@gmail.com', 'password': ['Passw0rd#'], "_id": "password_is_not_string"},
    ], ids=lambda x: "{}".format(x["_id"]))
    def test_invalid_login(self, api_client, credentials):
        credentials.pop('_id')
        resp = api_client.post('login/', data=credentials)
        assert resp.status_code == requests.codes.unauthorized, \
            "Login succeeded with invalid data: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_index(self, api_client):
        resp = api_client.get('index/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get index page: {}, {}".format(resp.text, resp.reason)
        assert "Index page. Possible actions: /login, /register, /help" in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.positive
    def test_home(self, api_client):
        resp = api_client.get('home/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get home page: {}, {}".format(resp.text, resp.reason)
        assert resp.json().get('devices'), \
            "Failed to get devices list: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_nav(self, api_client):
        resp = api_client.get('navigation/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get home page: {}, {}".format(resp.text, resp.reason)
        assert "UI specific endpoint. Nothing there" in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.positive
    def test_device(self, api_client):
        resp = api_client.get('devices/0/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get home page: {}, {}".format(resp.text, resp.reason)
        device = resp.json()
        assert device.get('status'), \
            "Device status wasn't retrieved: {}, {}".format(resp.text, resp.reason)
        assert device.get('device_id') == 0, \
            "Wrong device was retrieved: {}, {}".format(resp.text, resp.reason)
        assert len(device.get('camera_config')) == 15, \
            "Wrong device config was retrieved: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    @pytest.mark.parametrize('url', [
        {'url': -1, "_id": "negative_id"},
        {'url': 10, "_id": "non_existing_id"},
        {'url': 0.1, "_id": "float_id"},
        {'url': 'one', "_id": "string_id"},
        {'url': {'url': 1}, "_id": "string_id"},
    ], ids=lambda x: "{}".format(x["_id"]))
    def test_invalid_get_device(self, api_client, url):
        url.pop("_id")
        resp = api_client.get('devices/{}/'.format(url.get('url')))
        assert resp.status_code in (requests.codes.bad_request, requests.codes.not_found), \
            "Failed to get home page: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    def test_content(self, api_client):
        resp = api_client.get('devices/0/content/')
        assert resp.status_code == requests.codes.bad_request, \
            "Content was got via API: {}, {}".format(resp.text, resp.reason)
        assert "Live streaming is not available via API" in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.negative
    def test_video(self, api_client):
        resp = api_client.get('devices/0/video/')
        assert resp.status_code == requests.codes.bad_request, \
            "Video content was got via API: {}, {}".format(resp.text, resp.reason)
        assert "Live streaming is not available via API" in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.positive
    def test_start_stop_monitor(self, api_client):
        resp = api_client.post('devices/0/start/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to start monitoring: {}, {}".format(resp.text, resp.reason)

        resp = api_client.post('devices/0/start/')
        assert resp.status_code == requests.codes.forbidden, \
            "Monitoring was started twice for the same device: {},{}".format(resp.text, resp.reason)

        resp = api_client.get('devices/0/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get device data: {}, {}".format(resp.text, resp.reason)
        device = resp.json()
        assert device.get('status') == 'Provisioning', \
            "Device status is incorrect: {}, {}".format(resp.text, resp.reason)

        resp = api_client.post('devices/0/stop/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to stop monitoring: {}, {}".format(resp.text, resp.reason)

        resp = api_client.post('devices/0/stop/')
        assert resp.status_code == requests.codes.forbidden, \
            "Monitoring was stopped twice for the same device: {},{}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_get_device_config(self, api_client):
        resp = api_client.get('devices/0/configuration')
        assert resp.status_code == requests.codes.ok, \
            "Failed to start monitoring: {}, {}".format(resp.text, resp.reason)

        config = resp.json()
        assert config.get('subscribers'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        assert config.get('fps'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        assert config.get('duration'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        assert config.get('device_id') == 0, \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_valid_config_update(self, api_client):
        data = {
            'subscribers': 'test@gmail.com',
            'duration': 20,
            'fps': 20.0,
        }
        resp = api_client.post('devices/0/configuration/', data=data)
        assert resp.status_code == requests.codes.ok, \
            "Failed edit config: {}, {}".format(resp.text, resp.reason)

        resp = api_client.get('devices/0/configuration/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to start monitoring: {}, {}".format(resp.text, resp.reason)
        config = resp.json()
        assert config.get('subscribers') == data.get('subscribers'), \
            "Invalid data was set: {}, {}".format(resp.text, resp.reason)
        assert config.get('duration') == data.get('duration'), \
            "Invalid data was set: {}, {}".format(resp.text, resp.reason)
        assert config.get('fps') == data.get('fps'), \
            "Invalid data was set: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    @pytest.mark.parametrize('update', [
        {'subscribers': 'test@', 'duration': 20, 'fps': 1, "_id": "invalid_email"},
        {'subscribers': 'test@gmail.com', 'duration': -1, 'fps': 1, "_id": "negative_duration"},
        {'subscribers': 'test@gmail.com', 'duration': 61, 'fps': 1, "_id": "too_large_duration"},
        {'subscribers': 'test@gmail.com', 'duration': 10, 'fps': 0, "_id": "too_small_fps"},
        {'subscribers': 'test@gmail.com', 'duration': 10, 'fps': 121, "_id": "too_large_fps"},
        {'duration': 10, 'fps': 25, "_id": "no_subscribers"},
        {'subscribers': 'test@gmail.com', 'fps': 25, "_id": "no_duration"},
        {'subscribers': 'test@gmail.com', 'duration': 10, "_id": "no_fps"},
        {'subscribers': ['test@gmail.com'], 'duration': 10, 'fps': 10, "_id": "subscribers_list"},
        {'subscribers': 'test@gmail.com', 'duration': 10.5, 'fps': 10, "_id": "duration_float"},
        {'subscribers': 'test@gmail.com', 'duration': 10, 'fps': '10', "_id": "fps_string"},
        {"_id": "empty"},
    ], ids=lambda x: "{}".format(x["_id"]))
    def test_invalid_config_update(self, api_client, update):
        update.pop("_id")
        resp = api_client.post('devices/0/configuration/', data=update)
        assert resp.status_code == requests.codes.bad_request, \
            "Config was edited: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    def test_logout(self, api_client):
        resp = api_client.get('logout/')
        assert resp.status_code == requests.codes.bad_request, \
            "Logout is possible via API: {}, {}".format(resp.text, resp.reason)
        assert "Logout is not available via API" in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.positive
    def test_register(self, api_client):
        user = {
            'email': 'test.email{}@mailinator.com'.format(randint(1, 100000000000)),
            'password': 'wertY00z'
        }
        resp = api_client.post('register/', data=user)
        assert resp.status_code == requests.codes.ok, \
            "Failed to register a user: {}, {}".format(resp.text, resp.reason)

        resp = api_client.post('login/', data=user)
        assert resp.status_code == requests.codes.ok, \
            "Failed to login with new user: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.negative
    def test_register_twice(self, api_client):
        user = {
            'email': 'test.email{}@mailinator.com'.format(randint(1, 100000000000)),
            'password': 'wertY00z'
        }
        resp = api_client.post('register/', data=user)
        assert resp.status_code == requests.codes.ok, \
            "Failed to register a user: {}, {}".format(resp.text, resp.reason)

        resp = api_client.post('register/', data=user)
        assert resp.status_code == requests.codes.unauthorized, \
            "It is possible to register twice with the same data: {}, {}".format(
                resp.text, resp.reason
            )
        assert "Invalid data specified: User with such email already exists." in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.negative
    @pytest.mark.parametrize('user', [
        {'email': 'test.email', 'password': 'wertY00z', "_id": "invalid_email"},
        {'email': 't@t.com', 'password': '', "_id": "empty_password"},
        {'email': 't@t.com', 'password': '1', "_id": "too_short_password"},
        {'email': 't@t.com', 'password': 'qwertyuiTq', "_id": "no_numbers_is_password"},
        {'email': 't@t.com', 'password': 'qwertyu88888', "_id": "no_cap_letters"},
        {'password': 'qwertyu88888R', "_id": "no_email"},
        {'email': 't@t.com', "_id": "no_password"},
        {'email': ['t@t.com'], 'password': 'wertY00z', "_id": "email_non_string"},
        {'email': 't@t.com', 'password': 1, "_id": "password_non_string"},
        {"_id": "empty"},
    ], ids=lambda x: "{}".format(x["_id"]))
    def test_invalid_register(self, api_client, user):
        resp = api_client.post('register/', data=user)
        assert resp.status_code == requests.codes.unauthorized, \
            "User with invalid input was registered: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_alerts(self, api_client):
        resp = api_client.get('alerts/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get alerts: {}, {}".format(resp.text, resp.reason)
        alerts = resp.json()
        assert alerts.get('total'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        assert alerts.get('by_day'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        assert alerts.get('by_webcam'), \
            "Incorrect response returned: {}, {}".format(resp.text, resp.reason)
        if alerts.get('total') > 0:
            assert len(alerts.get('by_day')) > 0, \
                "No alerts in by_day section: {}, {}".format(resp.text, resp.reason)
            assert len(alerts.get('by_webcam')) > 0, \
                "No alerts in by_webcame section: {}, {}".format(resp.text, resp.reason)

    @pytest.mark.positive
    def test_help(self, api_client):
        resp = api_client.get('help/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get help page: {}, {}".format(resp.text, resp.reason)
        assert "Help page. Visit /help/ page in your browser to see full content." in resp.text, \
            "Unknown response received: {}".format(resp.text)

    @pytest.mark.positive
    def test_documentation(self, api_client):
        resp = api_client.get('documentation/')
        assert resp.status_code == requests.codes.ok, \
            "Failed to get help page: {}, {}".format(resp.text, resp.reason)
        assert resp.json() == {
            'url': ['/static/docs/api_guide.pdf', '/static/docs/user_guide.pdf']
        }, "Wrong url list was retrieved - {}: {}, {}".format(resp.json(), resp.text, resp.reason)
