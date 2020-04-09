"""Test deploying a base line static site."""
import os
import logging
import time
from runway.util import change_dir

from integration_tests.test_staticsite.test_staticsite import StaticSite
from integration_tests.util import run_command

from integration_tests.test_staticsite.pages.login_page import LoginPage
from integration_tests.test_staticsite.pages.home_page import HomePage

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import boto3


LOGGER = logging.getLogger(__name__)


class TestAuthAtEdgeLogin(StaticSite):
    """Test deploying a base line static site."""

    TEST_NAME = __name__
    module_dir = 'auth-at-edge-e2e'
    driver = None
    login_page = None
    home_page = None

    cloudformation = boto3.client('cloudformation', region_name='us-east-1')
    cognito = boto3.client('cognito-idp', region_name='us-east-1')

    def deploy(self):
        """Deploy provider."""
        os.mkdir(os.path.join(self.staticsite_test_dir, self.module_dir))
        os.mkdir(os.path.join(self.staticsite_test_dir, self.module_dir, 'build'))
        self.copy_runway('auth-at-edge-e2e')
        with change_dir(self.staticsite_test_dir):
            return run_command(['runway', 'deploy'])

    def run(self):
        """Run tests."""
        self.clean()
        self.set_env_var('CI', '1')
        assert self.deploy() == 0, '{}: Auth@Edge Site failed'.format(__name__)

        self.e2e_setup()
        self.test_for_invalid_credentials()
        self.test_for_successful_login()

    def e2e_setup(self):
        stack = self.cloudformation.describe_stacks(
            StackName='dev-auth-at-edge-e2e'
        )
        distribution_domain = [
            output for output in
            stack['Stacks'][0]['Outputs'] if
            output.get('OutputKey') == 'CFDistributionDomainName'
        ][0].get('OutputValue')
        self.driver = webdriver.Chrome()
        self.driver.set_window_size(1200, 800)
        self.login_page = LoginPage(self.driver, 'https://%s' % distribution_domain)
        self.home_page = HomePage(self.driver, 'https://%s' % distribution_domain)

    def test_for_invalid_credentials(self):
        self.login_page.goto_base_url()
        self.login_page.login('foo', 'bar')
        assert self.login_page.verify_credentials_invalid()

    def test_for_successful_login(self):
        stack = self.cloudformation.describe_stacks(
            StackName='dev-auth-at-edge-e2e-dependencies'
        )
        user_pool_id = [
            output for output in
            stack['Stacks'][0]['Outputs'] if
            output.get('OutputKey') == 'AuthAtEdgeUserPoolId'
        ][0].get('OutputValue')

        self.cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username='foo@rackspace.com',
            TemporaryPassword='P@ssw0rd',
            MessageAction='SUPPRESS'
        )

        self.login_page.goto_base_url()
        self.login_page.login('foo@rackspace.com', 'P@ssw0rd')
        assert self.home_page.verify_app_logo_visible()

    def teardown(self):
        self.driver.quit()
        self.logger.info('Tearing down: %s', self.TEST_NAME)
        self.delete_venv(self.module_dir)
        with change_dir(self.staticsite_test_dir):
            run_command(['runway', 'destroy'])
        self.clean()
