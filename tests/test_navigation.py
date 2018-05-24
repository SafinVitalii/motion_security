from random import randint

import pytest
import time
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


class TestUserInterface(object):
    def test_device_page(self, app):
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(0.25)
        assert app.find_element_by_id('config').is_displayed()
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()
        assert app.find_element_by_id('home').is_displayed()
        assert app.find_element_by_id('live').is_displayed()

    def test_device_live(self, app):
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(0.25)
        assert app.find_element_by_id('config').is_displayed()
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()
        assert app.find_element_by_id('home').is_displayed()
        assert app.find_element_by_id('live').is_displayed()
        app.find_element_by_id('live').click()
        time.sleep(0.25)
        assert app.find_element_by_id('stream').is_displayed()
        assert app.find_element_by_id('back').is_displayed()
        assert app.find_element_by_id('stream').size['height'] == 480
        assert app.find_element_by_id('stream').size['width'] == 640
        app.find_element_by_id('back').click()

    def test_help_page(self, driver):
        driver.find_element_by_id('help').click()
        time.sleep(0.5)
        assert driver.find_element_by_id('head').is_displayed()
        assert driver.find_element_by_id('home').is_displayed()

    def test_documentation_page(self, app):
        app.find_element_by_id('documentation').click()
        time.sleep(0.5)
        assert app.find_element_by_id('guide').is_displayed()
        assert app.find_element_by_id('api').is_displayed()
        assert app.find_element_by_id('home').is_displayed()

    def test_register(self, driver):
        driver.find_element_by_id('register').click()
        time.sleep(0.25)
        driver.find_element_by_id('email').send_keys(
            "test{}@gmail.com".format(randint(1, 1000000000))
        )
        driver.find_element_by_id('password').send_keys("Passw0rd#")
        driver.find_element_by_id('register').submit()
        time.sleep(0.5)
        driver.find_element_by_id('login').click()
        time.sleep(0.25)
        driver.find_element_by_id('email').send_keys("test@gmail.com")
        driver.find_element_by_id('password').send_keys("Passw0rd#")
        driver.find_element_by_id('login').submit()
        time.sleep(0.5)
        assert driver.find_element_by_css_selector('.page-content').is_displayed()

    def test_edit_device_configuration(self, app):
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(0.25)
        assert app.find_element_by_id('config').is_displayed()
        app.find_element_by_id('config').click()
        time.sleep(0.25)
        assert app.find_element_by_id('subscribers').is_displayed()
        assert app.find_element_by_id('duration').is_displayed()
        assert app.find_element_by_id('fps').is_displayed()
        assert app.find_element_by_id('back').is_displayed()

        app.find_element_by_id('duration').clear()
        app.find_element_by_id('duration').send_keys("20")
        app.find_element_by_css_selector('input[type=submit]').submit()
        time.sleep(0.5)
        app.refresh()
        time.sleep(1)
        assert app.find_element_by_id('duration').get_attribute('value') == '20'
