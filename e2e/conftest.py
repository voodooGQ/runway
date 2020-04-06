import pytest
import sys
from selenium import webdriver


# tell python where our modules are...
sys.path.append('pages')
sys.dont_write_bytecode = True

# add cli options...
def pytest_addoption(parser):
    parser.addoption('--driver', action='store', default='chrome')

# driver fixture passed to all tests
@pytest.fixture(scope='session')
def driver(request):
    driver = webdriver.Chrome()
    driver.set_window_size(1200, 800)
    yield driver
    driver.quit()
