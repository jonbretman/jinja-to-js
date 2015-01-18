from __future__ import absolute_import, unicode_literals
import json
import os
import subprocess
from os.path import abspath, join, dirname
import tempfile
import unittest
from nose.tools import eq_ as equal
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja_to_js import compile_template


class Tests(unittest.TestCase):

    ROOT = abspath(join(dirname(__file__)))
    TEMPLATE_PATH = os.path.join(ROOT, 'templates')
    NODE_SCRIPT_PATH = os.path.join(ROOT, 'render_underscore_template.js')

    def setUp(self):
        self.loader = FileSystemLoader(self.TEMPLATE_PATH)
        self.env = Environment(loader=self.loader, extensions=['jinja2.ext.with_'])

    def test_if(self):
        self._run_test('if', foo=False, bar=True)

    def test_interpolation(self):
        self._run_test('interpolation',
                       key='value',
                       obj=dict(
                           key='value',
                           other_obj=dict(
                               key='value'
                           )
                       ))

    def test_iteration_iteritems(self):
        self._run_test('iteration_iteritems', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_items(self):
        self._run_test('iteration_items', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_values(self):
        self._run_test('iteration_values', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_list(self):
        self._run_test('iteration_list', values=[1, 2, 3])

    def test_iteration_keys(self):
        self._run_test('iteration_keys', thing=dict(
            key='value'
        ))

    def test_with(self):
        self._run_test('with', foo='foo', bar='bar')

    def test_set(self):
        self._run_test('set')

    def test_safe_filter(self):
        self._run_test('safe_filter', foo='&lt;div&gt;')

    def test_conditions(self):
        self._run_test('conditions',
                       foo=False, bar=6, baz=3,
                       person='jimmy', fizz=5, buzz=5)

    def test_loop_helpers(self):
        self._run_test('loop_helpers', things=[1, 2, 3, 4, 5, 6])

    def test_tests(self):
        self._run_test('tests', age=30)

    def _run_test(self, name, **kwargs):

        # first we'll render the jinja template
        jinja_result = self.env.get_template('%s.jinja' % name).render(**kwargs).strip()

        underscore_template_str = compile_template(self.env, self.loader, '%s.jinja' % name)

        # now create a temp file containing the compiled underscore template
        underscore_file, underscore_file_path = tempfile.mkstemp()
        os.fdopen(underscore_file, 'w').write(
            underscore_template_str
        )

        # and another temp file containing the data
        data_file, data_file_path = tempfile.mkstemp()
        os.fdopen(data_file, 'w').write(json.dumps(kwargs))

        # get the result of rendering the underscore template
        try:
            js_result = subprocess.check_output(
                ['node',
                 self.NODE_SCRIPT_PATH,
                 underscore_file_path,
                 data_file_path]
            )
        except Exception as e:
            raise e
        finally:
            # remove the temp files
            os.unlink(data_file_path)
            os.unlink(underscore_file_path)

        # check the jinja result and the underscore result are the same
        equal(jinja_result.strip(), js_result.strip())
