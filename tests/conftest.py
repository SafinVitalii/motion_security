import pytest
import time
import requests
from selenium import webdriver


@pytest.fixture()
def driver():
    d = webdriver.Chrome('/home/vitalii/chromedriver')
    d.get('http://127.0.0.1:5000')
    yield d
    d.quit()


@pytest.fixture()
def app(driver):
    driver.find_element_by_id('login').click()
    time.sleep(0.25)
    driver.find_element_by_id('email').send_keys("test@gmail.com")
    driver.find_element_by_id('password').send_keys("Passw0rd#")
    driver.find_element_by_id('login').submit()
    time.sleep(0.5)
    return driver


@pytest.fixture(scope='module')
def api_client():
    return APIClient()


class APIClient(object):
    def __init__(self):
        self.url = 'http://127.0.0.1:5000/'
        self.auth = {'email': 'test@gmail.com', 'password': 'Passw0rd#'}
        self.token = requests.post(self.url + 'login/', json=self.auth,
                                   headers={'Content-Type': 'application/json'}).json()
        self.headers = {'Content-Type': 'application/json', 'Auth-Token': self.token}

    def get(self, url, headers=None):
        headers = headers if headers else self.headers
        print "Sending GET request: {}, headers: {}".format(
            self.url + url, headers
        )
        resp = requests.get(self.url + url, headers=headers)
        print "Received response: {} ({}), {}".format(resp.reason, resp.status_code, resp.text)
        return resp

    def post(self, url, data=None, headers=None):
        headers = headers if headers else self.headers
        print "Sending POST request: {}, data: {}, headers: {}".format(
            self.url + url, data, headers
        )
        resp = requests.post(self.url + url, json=data, headers=headers)
        print "Received response: {} ({}), {}".format(resp.reason, resp.status_code, resp.text)
        return resp
