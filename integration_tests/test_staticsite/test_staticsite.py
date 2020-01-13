"""Tests for the StaticSite module."""
import os
import glob

from send2trash import send2trash

from integration_tests.integration_test import IntegrationTest
from integration_tests.util import (copy_file, copy_dir, import_tests,
                                    execute_tests)


class StaticSite(IntegrationTest):
    """Test StaticSite based module scenarios"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    fixtures_dir = os.path.join(base_dir, 'fixtures')
    tests_dir = os.path.join(base_dir, 'tests')

    staticsite_test_dir = os.path.join(base_dir, 'staticsite_test')

    def copy_fixture(self, name='basic-site'):
        """Copy fixture files for test"""
        copy_dir(
            os.path.join(self.fixtures_dir, name),
            os.path.join(self.staticsite_test_dir, name)
        )

    def copy_runway(self, template):
        """Copy runway template to proper directory."""
        template_file = os.path.join(self.fixtures_dir, 'runway-{}.yml'.format(template))
        copy_file(template_file, os.path.join(self.staticsite_test_dir, 'runway.yml'))

    def run(self):
        """Find all tests and run them."""
        import_tests(self.logger, self.tests_dir, 'test_*')
        tests = [test(self.logger) for test in StaticSite.__subclasses__()]
        if not tests:
            raise Exception('No tests were found.')
        self.logger.debug('FOUND TESTS: %s', tests)
        self.set_environment('dev')
        self.set_env_var('PIPENV_VENV_IN_PROJECT', '1')
        err_count = execute_tests(tests, self.logger)
        assert err_count == 0  # assert that all subtests were successful
        return err_count

    def clean(self):
        """Clean up StaticSite module directory."""
        file_types = ('*.yaml', '*.yml')
        templates = []
        for file_type in file_types:
            templates.extend(glob.glob(os.path.join(self.staticsite_test_dir, file_type)))
        for template in templates:
            if os.path.isfile(template):
                self.logger.debug('send2trash: "%s"', template)
                send2trash(template)
        folders = ['basic-site']
        for folder in folders:
            folder_path = os.path.join(self.staticsite_test_dir, folder)
            if os.path.isdir(folder_path):
                self.logger.debug('send2trash: "%s"', folder_path)
                send2trash(folder_path)

    def delete_venv(self, module_directory):
        """Delete pipenv venv before running destroy."""
        folder_path = os.path.join(self.staticsite_test_dir,
                                   f'{module_directory}/.venv')
        if os.path.isdir(folder_path):
            self.logger.debug('send2trash: "%s"', folder_path)
            send2trash(folder_path)

    def teardown(self):
        """Teardown resources create during init."""
        self.unset_env_var('PIPENV_VENV_IN_PROJECT')
        self.clean()
