from ..base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    page_title = (By.CSS_SELECTOR, '.page-title')
    def __init__(self, driver):
        super(LoginPage, self).__init__(driver)

    def loaded(self):
        self.wait_for_element(self.page_title)
