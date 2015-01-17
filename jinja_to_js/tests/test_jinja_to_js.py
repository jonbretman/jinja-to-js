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
              open(self._template_path('%s.html' % name)).read().strip())

    def setUp(self):
        self.env = Environment(extensions=['jinja2.ext.with_'])
        self.loader = FileSystemLoader(self._template_path())

    def test_if(self):
        self._run_test('if')

    def test_if_else(self):
        self._run_test('if_else')

    def test_if_else_if(self):
        self._run_test('if_else_if')

    def test_interpolation(self):
        self._run_test('interpolation')

    def test_iteration_iteritems(self):
        self._run_test('iteration_iteritems')

    def test_iteration_items(self):
        self._run_test('iteration_items')

    def test_iteration_values(self):
        self._run_test('iteration_values')

    def test_iteration_list(self):
        self._run_test('iteration_list')

    def test_iteration_keys(self):
        self._run_test('iteration_keys')

    def test_with(self):
        self._run_test('with')
