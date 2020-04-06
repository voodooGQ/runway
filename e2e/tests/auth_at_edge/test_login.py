import pytest
import logging
from requests import get
from ...pages.auth_at_edge.login_page import LoginPage
from ...runner import Runner
from runway.util import change_dir
from integration_tests.integration_test import IntegrationTest
from integration_tests.util import run_command

LOGGER = logging.getLogger(__name__)

class TestThing():
    @pytest.fixture(scope="module", autouse=True)
    def setup(self, driver):
        global runner
        runner = Runner('Test Login')

        try:
            global loginPage
            runner.copy_fixture('e2e-auth-at-edge')
            runner.copy_runway('auth-at-edge')
            with change_dir(runner.temp_dir):
                integrationTest = IntegrationTest(LOGGER)
                integrationTest.set_environment('dev')
                integrationTest.set_env_var('PIPENV_VENV_IN_PROJECT', '1')
                assert self.deploy() == 0, '{}: E2E A@E Failed'.format(__name__)
                yield
                runner.clean()
        except:
            runner.clean()

    def deploy(self):
        integrationTest = IntegrationTest(LOGGER)
        integrationTest.set_environment('dev')
        integrationTest.set_env_var('PIPENV_VENV_IN_PROJECT', '1')
        return run_command(['runway', 'deploy'])


    def test_login_returns_status_200(driver):
        res = get(loginPage.get_base_url())

        assert res.status_code == 200

    def test_for_correct_page_title(driver):
        assert loginPage.page_title_equals('Shane Smith')
