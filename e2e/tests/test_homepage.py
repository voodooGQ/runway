import pytest
from ..pages.qs_page import QsPage
from ..pages.github_page import GithubPage

'''
autouse fixture sets up page objects and opens site
and module scope ensures it runs only once
'''
@pytest.fixture(scope="module", autouse=True)
def setup(driver):
    # makes pages available to all tests
    global qsPage, githubPage
    qsPage = QsPage(driver)
    githubPage = GithubPage(driver)
    # goto our test site
    qsPage.goto(qsPage.url)

# tests MUST start with `test_` to run with pytest
def test_should_display_5_posts(driver):
    assert qsPage.get_num_posts() is 5

def test_should_open_link_in_new_window(driver):
    qsPage.element(qsPage.github_link).click()
    githubPage.switch_to_new_window()

    assert githubPage.element_exits(githubPage.username) is True

    # cleanup...
    qsPage.switch_to_first_window()

def test_sidebar_has_a_set_width(driver):
    assert qsPage.element(qsPage.sidebar).size['width'] == 280

def test_find_post_by_paging(driver):
    post_title = 'When To Automate'
    qsPage.find_post_by_paging(post_title)

    assert qsPage.find_post_by_paging(post_title) is True
