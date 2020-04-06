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
    runner = Runner("Test Login")
    integration_test = IntegrationTest(LOGGER)
    login_page = None

    @pytest.fixture(scope="module", autouse=True)
    def setup(self, driver):
        try:
            self.runner.copy_fixture('e2e-auth-at-edge')
            self.runner.copy_runway('auth-at-edge')
            with change_dir(self.runner.temp_dir):
                assert self.deploy() == 0, '{}: E2E A@E Failed'.format(__name__)
                self.login_page = LoginPage(driver, 'https://shaneallensmith.com')
                yield
                self.teardown()
        except Exception:  # pylint: disable=broad-except
            self.teardown()

    def deploy(self):
        self.integration_test.set_environment('dev')
        self.integration_test.set_env_var('PIPENV_VENV_IN_PROJECT', '1')
        self.integration_test.set_env_var('CI', '1')
        return run_command(['runway', 'deploy'])

    def teardown(self):
        try:
            with change_dir(self.runner.temp_dir):
                run_command(['runway', 'destroy'])
        finally:
            self.runner.clean()

    def test_login_returns_status_200(self, driver):
        res = get(self.login_page.get_base_url())
        assert res.status_code == 200

    def test_for_correct_page_title(self, driver):
        assert self.login_page.page_title_equals('Shane Smith')
