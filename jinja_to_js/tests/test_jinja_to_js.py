from __future__ import absolute_import, unicode_literals
import os
from os.path import abspath, join, dirname
import unittest
from nose.tools import eq_ as equal
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja_to_js import compile_template


class Tests(unittest.TestCase):

    ROOT = abspath(join(dirname(__file__)))

    def _template_path(self, filename=''):
        return os.path.join(self.ROOT, 'templates', filename)

    def _run_test(self, name):
        equal(compile_template(self.env, self.loader, '%s.jinja' % name),
              open(self._template_path('%s_expected.html' % name)).read().strip())

    def setUp(self):
        self.env = Environment()
        self.loader = FileSystemLoader(self._template_path())

    def test_compile_template(self):
        self._run_test('simple')
