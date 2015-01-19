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
from jinja_to_js import JinjaToJS


class Tests(unittest.TestCase):

    ROOT = abspath(join(dirname(__file__)))
    TEMPLATE_PATH = os.path.join(ROOT, 'templates')
    NODE_SCRIPT_PATH = os.path.join(ROOT, 'render_underscore_template.js')

    def setUp(self):
        self.loader = FileSystemLoader(self.TEMPLATE_PATH)
        self.env = Environment(loader=self.loader, extensions=['jinja2.ext.with_'])

    def test_if(self):
        self._run_test('if.jinja', foo=False, bar=True)

    def test_interpolation(self):
        self._run_test('interpolation.jinja',
                       key='value',
                       obj=dict(
                           key='value',
                           other_obj=dict(
                               key='value'
                           )
                       ))

    def test_iteration_iteritems(self):
        self._run_test('iteration_iteritems.jinja', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_items(self):
        self._run_test('iteration_items.jinja', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_values(self):
        self._run_test('iteration_values.jinja', thing=dict(
            one='one',
            two='two',
            three='three'
        ))

    def test_iteration_list(self):
        self._run_test('iteration_list.jinja', values=[1, 2, 3, 4, 5, 6])

    def test_iteration_keys(self):
        self._run_test('iteration_keys.jinja', thing=dict(
            key='value'
        ))

    def test_with(self):
        self._run_test('with.jinja', foo='foo', bar='bar')

    def test_set(self):
        self._run_test('set.jinja')

    def test_safe_filter(self):
        self._run_test('safe_filter.jinja', foo='&lt;div&gt;', obj=dict(key='&lt;div&gt;'))

    def test_conditions(self):
        self._run_test('conditions.jinja',
                       foo=False, bar=6, baz=3,
                       person='jimmy', fizz=5, buzz=5)

    def test_loop_helpers(self):
        self._run_test('loop_helpers.jinja', things=[1, 2, 3, 4, 5, 6])

    def test_tests(self):
        self._run_test('tests.jinja', age=30)

    def test_truthy_falsey_values(self):
        self._run_test('truthy_falsey_values.jinja',
                       non_empty_array=[1, 2, 3],
                       empty_array=[],
                       empty_object={},
                       non_empty_object=dict(one='one'),
                       empty_string='',
                       non_empty_string='hello')

    def test_comparisons(self):
        self._run_test('comparisons.jinja',
                       list_a=[1, 2, 3],
                       list_b=[1, 2, 3],
                       list_c=[2, 3, 4],
                       dict_a=dict(one='one'),
                       dict_b=dict(one='one'),
                       dict_c=dict(two='two'))

    def test_include(self):
        self._run_test('include.jinja',
                       additional=['includes/name.jinja'],
                       the_beatles=['John', 'Paul', 'George', 'Ringo'])

    def test_math(self):
        self._run_test('math.jinja')

    def test_extends(self):
        self._run_test('extends.jinja')

    def _run_test(self, name, additional=None, **kwargs):

        tmp_file_paths = []

        # first we'll render the jinja template
        jinja_result = self.env.get_template(name).render(**kwargs).strip()

        # create the main template
        arg, path = self._compile_js_template(name)
        tmp_file_paths.append(path)
        template_args = [arg]

        # create a temp file containing the data
        data_file, data_file_path = tempfile.mkstemp()
        os.fdopen(data_file, 'w').write(json.dumps(kwargs))

        # if additional template are required e.g. for includes then create those too
        if additional:
            for n in additional:
                arg, path = self._compile_js_template(n)
                tmp_file_paths.append(path)
                template_args.append(arg)

        # get the result of rendering the underscore template
        try:
            js_result = subprocess.check_output(
                ['node',
                 self.NODE_SCRIPT_PATH]
                + template_args +
                [data_file_path]
            )
        except Exception as e:
            raise e
        finally:
            # remove the temp files
            for path in tmp_file_paths:
                os.unlink(path)

        # check the jinja result and the underscore result are the same
        equal(jinja_result.strip(), js_result.strip())

    def _compile_js_template(self, name):
        print name
        underscore_template_str = JinjaToJS(self.env, template_name=name).get_output()
        print underscore_template_str
        fd, file_path = tempfile.mkstemp()
        os.fdopen(fd, 'w').write(
            underscore_template_str
        )
        return name + ':' + file_path, file_path
