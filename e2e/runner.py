import os
from integration_tests.util import (copy_file, copy_dir)


class Runner(object):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    fixtures_dir = os.path.join(base_dir, 'fixtures')
    temp_dir = os.path.join(base_dir, 'tmp')

    def __init__(self, name="Test Runner"):
        self.name = name

    def copy_fixture(self, name=''):
        """Copy fixture files for test"""
        copy_dir(
            os.path.join(self.fixtures_dir, name),
            os.path.join(self.temp_dir, name)
        )

    def copy_runway(self, template):
        """Copy runway template to proper directory."""
        template_file = os.path.join(
            self.fixtures_dir, 'runway-{}.yml'.format(template)
        )
        copy_file(template_file, os.path.join(self.temp_dir, 'runway.yml'))
