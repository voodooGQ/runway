"""Tests for the Path type object."""
import logging
import unittest

from runway.path import Path

LOGGER = logging.getLogger('runway')


class PathTester(unittest.TestCase):
    """Test Path class."""

    def test_parse_local_source_string(self):
        """Parsing location source string. Verify tuple is parsed as anticipated."""
        (source, uri, location, options) = Path.parse({'path': 'src/foo/bar'})
        self.assertEqual(source, 'local')
        self.assertEqual(location, 'src/foo/bar')
        self.assertEqual(uri, '')
        self.assertEqual(options, {})

    def test_parse_git_source_no_location_or_options(self):
        """Parsing Git source with no location or options. Verify tuple is parsed as anticipated."""
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git'}
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, '/')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {})

    def test_parse_git_source_with_location_no_options(self):
        """Parsing Git source with location, no options. Verify tuple is parsed as anticipated."""
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git//foo/bar'}
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, 'foo/bar')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {})

    def test_parse_git_source_with_options_no_location(self):
        """
        Parsing Git source with options, no location.

        Verify tuple is parsed as anticipated.
        """
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git?branch=foo'}
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, '/')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {'branch': 'foo'})

    def test_parse_git_source_with_multiple_options_no_location(self):
        """
        Parsing Git source with multiple options, no location.

        Verify tuple is parsed as anticipated.
        """
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git?branch=foo&bar=baz'}
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, '/')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {'branch': 'foo', 'bar': 'baz'})

    def test_parse_git_source_with_options_and_location(self):
        """
        Parsing Git source with options and location

        Verify tuple is parsed as anticipated.
        """
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git//src/foo/bar?branch=foo'}
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, 'src/foo/bar')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {'branch': 'foo'})

    def test_parse_git_source_with_multiple_options_and_location(self):
        """
        Parsing Git source with multiple options and location

        Verify tuple is parsed as anticipated.
        """
        (source, uri, location, options) = Path.parse(
            {'path': 'git::git://github.com/onicagroup/foo/bar.git//src/foo/bar?branch=foo&bar=baz'} # noqa E501
        )
        self.assertEqual(source, 'git')
        self.assertEqual(location, 'src/foo/bar')
        self.assertEqual(uri, 'git://github.com/onicagroup/foo/bar.git')
        self.assertEqual(options, {'branch': 'foo', 'bar': 'baz'})
