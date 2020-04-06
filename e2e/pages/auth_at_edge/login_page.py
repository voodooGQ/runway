from ..base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    page_title = (By.CSS_SELECTOR, '.page-title')

    def loaded(self):
        self.wait_for_element(self.page_title)

    def page_title_equals(self, title):
        elem = self.element(self.page_title).text
        return elem == title
