from random import randint

import time

default_timeout = 0.25


class TestUserInterface(object):
    def test_device_page(self, app):
        """ Verify navigation to device page """
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('config').is_displayed()
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()
        assert app.find_element_by_id('live').is_displayed()

    def test_device_live(self, app):
        """ Verify live streaming from device """
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('config').is_displayed()
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()
        assert app.find_element_by_id('live').is_displayed()
        app.find_element_by_id('live').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('stream').is_displayed()
        assert app.find_element_by_id('back').is_displayed()
        assert app.find_element_by_id('stream').size['height'] >= 480
        assert app.find_element_by_id('stream').size['width'] >= 640
        app.find_element_by_id('back').click()

    def test_help_page(self, app):
        """ Verify navigation to help page via header links """
        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)

        app.find_element_by_id('help_link').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('head').is_displayed()

    def test_documentation_page(self, app):
        """ Verify navigation to documentation page """
        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)

        app.find_element_by_id('doc_link').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('guide').is_displayed()
        assert app.find_element_by_id('api').is_displayed()
        assert app.find_element_by_id('home').is_displayed()

    def test_register(self, driver):
        """ Verify registration process """
        driver.find_element_by_id('register').click()
        time.sleep(default_timeout)
        driver.find_element_by_id('email').send_keys(
            "test{}@gmail.com".format(randint(1, 1000000000))
        )
        driver.find_element_by_id('password').send_keys("Passw0rd#")
        driver.find_element_by_id('register').submit()
        time.sleep(default_timeout * 2)
        driver.find_element_by_id('login').click()
        time.sleep(default_timeout)
        driver.find_element_by_id('email').send_keys("test@gmail.com")
        driver.find_element_by_id('password').send_keys("Passw0rd#")
        driver.find_element_by_id('login').submit()
        time.sleep(default_timeout * 2)
        assert driver.find_element_by_css_selector('.page-content').is_displayed()
        assert driver.find_element_by_id('alertChart').is_displayed()

    def test_edit_device_configuration(self, app):
        """ Verify that device configuration is changed and set for Monitor instance """
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('config').is_displayed()
        app.find_element_by_id('config').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('subscribers').is_displayed()
        assert app.find_element_by_id('duration').is_displayed()
        assert app.find_element_by_id('fps').is_displayed()
        assert app.find_element_by_id('back').is_displayed()

        app.find_element_by_id('duration').clear()
        app.find_element_by_id('duration').send_keys("20")
        app.find_element_by_css_selector('input[type=submit]').submit()
        time.sleep(default_timeout * 2)
        app.refresh()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('duration').get_attribute('value') == '20'

    def test_invalid_login(self, driver):
        """ Verify that it is not possible to login with non-existing credentials """
        driver.find_element_by_id('login').click()
        time.sleep(default_timeout)
        driver.find_element_by_id('email').send_keys("notfound@gmail.com")
        driver.find_element_by_id('password').send_keys("password")
        driver.find_element_by_id('login').submit()
        time.sleep(1)
        assert driver.find_element_by_id("error").text == \
               'Error occured when logging in. Please verify your credentials.'

    def test_login_logout(self, app):
        """ Verify logout operation """
        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)

        app.find_element_by_id('logout_link').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('login').is_displayed()

    def test_change_device_status(self, app):
        """ Verify changing device status to 'Provisioning' and back to 'Available' """
        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()

        app.find_element_by_id('start').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('success_message').text == 'Monitoring has started.'

        app.find_element_by_id('start').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('error_message').text == \
               'Failed to start monitoring for this camera.'

        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)
        app.find_element_by_id('home_link').click()
        time.sleep(default_timeout * 2)

        assert 'Provisioning' in \
               app.find_element_by_xpath('//a[.=" Camera 0 "]/parent::*/parent::*').text

        app.find_element_by_xpath('//a[.=" Camera 0 "]').click()
        time.sleep(default_timeout)
        assert app.find_element_by_id('start').is_displayed()
        assert app.find_element_by_id('stop').is_displayed()

        app.find_element_by_id('stop').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('success_message').text == 'Monitoring was stopped.'

        app.find_element_by_id('stop').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('error_message').text == 'Failed to stop monitoring.'

        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)
        app.find_element_by_id('home_link').click()
        time.sleep(default_timeout * 2)

        assert 'Available' in \
               app.find_element_by_xpath('//a[.=" Camera 0 "]/parent::*/parent::*').text

    def test_alerts_page(self, app):
        """ Verify navigation to alerts page """
        i_frame = app.find_elements_by_tag_name('iframe')[0]
        app.switch_to_default_content()
        app.switch_to_frame(i_frame)

        app.find_element_by_id('alerts_link').click()
        time.sleep(default_timeout * 2)
        assert app.find_element_by_id('alerts_by_day').is_displayed()
        assert app.find_element_by_id('alerts_by_camera').is_displayed()
