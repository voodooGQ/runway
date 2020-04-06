import pytest
from requests import get
from ...pages.auth_at_edge.login_page import LoginPage

@pytest.fixture(scope="module", autouse=True)
def setup(driver):
    global loginPage
    loginPage = LoginPage(driver, 'https://shaneallensmith.com')
    loginPage.goto('/')

def test_login_returns_status_200(driver):
    res = get(loginPage.get_base_url())

    assert res.status_code == 200

def test_for_correct_page_title(driver):
    assert loginPage.page_title_equals('Shane Smith')
