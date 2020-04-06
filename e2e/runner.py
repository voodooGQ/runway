import os
import logging

from send2trash import send2trash

from integration_tests.util import (copy_file, copy_dir)

LOGGER = logging.getLogger(__name__)


class Runner(object):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    fixtures_dir = os.path.join(base_dir, 'fixtures')
    temp_dir = os.path.join(base_dir, 'tmp')

    fixture_dir = ''
    runway_file = ''

    def __init__(self, name="Test Runner"):
        self.name = name

    def copy_fixture(self, name=''):
        """Copy fixture files for test"""
        copy_dir(
            os.path.join(self.fixtures_dir, name),
            os.path.join(self.temp_dir, name)
        )
        self.fixture_dir = os.path.join(self.temp_dir, name)

    def copy_runway(self, template):
        """Copy runway template to proper directory."""
        template_file = os.path.join(
            self.fixtures_dir, 'runway-{}.yml'.format(template)
        )
        copy_file(
            template_file,
            os.path.join(self.temp_dir, 'runway.yml')
        )
        self.runway_file = os.path.join(self.temp_dir, 'runway.yml')

    def clean(self):
        if os.path.isdir(self.fixture_dir):
            LOGGER.debug('send2trash: "%s"', self.fixture_dir)
            send2trash(self.fixture_dir)
        if os.path.isfile(self.runway_file):
            LOGGER.debug('send2trash: "%s"', self.runway_file)
            send2trash(self.runway_file)

