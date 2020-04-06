import pytest
from requests import get
from ...pages.auth_at_edge.login_page import LoginPage
from ...runner import Runner


@pytest.fixture(scope="module", autouse=True)
def setup(driver):
    global loginPage
    global runner
    runner = Runner('Test Login')
    runner.copy_fixture('e2e-auth-at-edge')
    runner.copy_runway('auth-at-edge')
    loginPage = LoginPage(driver, 'https://shaneallensmith.com')
    loginPage.goto('/')
    yield
    runner.clean()

def test_login_returns_status_200(driver):
    res = get(loginPage.get_base_url())

    assert res.status_code == 200

def test_for_correct_page_title(driver):
    assert loginPage.page_title_equals('Shane Smith')
