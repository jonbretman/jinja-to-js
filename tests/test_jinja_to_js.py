from __future__ import absolute_import, unicode_literals
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from os.path import abspath, dirname, join

from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader

import pytest

from jinja_to_js import JinjaToJS, is_method_call


if "check_output" not in dir( subprocess ):
    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
else:
    check_output = subprocess.check_output


class Encoder(json.JSONEncoder):
    def default(self, o):
        if callable(o):
            # since JSON cannot encode functions we just need a way of
            # telling the node script to add one into the context
            return '<<< MAKE ME A FUNCTION >>>'
        if hasattr(o, '__dict__'):
            return o.__dict__
        return super(Encoder, self).default(o)


class Tests(unittest.TestCase):

    ROOT = abspath(join(dirname(__file__)))
    TEMPLATE_PATH = os.path.join(ROOT, 'templates')
    NODE_SCRIPT_PATH = os.path.join(ROOT, 'render_template.js')

    def setUp(self):
        self.loader = FileSystemLoader(self.TEMPLATE_PATH)
        self.env = Environment(loader=self.loader, autoescape=True, extensions=['jinja2.ext.with_'])
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_constructor_exceptions(self):

        with pytest.raises(ValueError) as e:
            JinjaToJS()

        assert str(e.value) == 'Either a template_name or template_string must be provided.'

    def test_is_method_call(self):
        node = self.env.parse('{{ foo() }}').find(nodes.Call)
        assert is_method_call(node, 'foo') is True
        assert is_method_call(node, 'bar') is False

        node = self.env.parse('{{ foo }}').find(nodes.Name)
        assert is_method_call(node, 'foo') is False

        node = nodes.Call()
        node.node = None
        assert is_method_call(node, 'foo') is False

        node = self.env.parse('{{ foo.bar.baz() }}').find(nodes.Call)
        assert is_method_call(node, 'baz') is True
        assert is_method_call(node, 'bar') is False
        assert is_method_call(node, 'foo') is False
        assert is_method_call(node, ('foo', 'bar', 'baz')) is True

        node = self.env.parse('{{ foo["bar"]() }}').find(nodes.Call)
        assert is_method_call(node, 'bar') is True

    def test_exception_raised_for_unknown_node(self):
        compiler = JinjaToJS(template_string='hello')

        class FakeNode(object):
            pass

        fake_node = FakeNode()

        with pytest.raises(Exception) as e:
            compiler._process_node(fake_node)

        assert str(e.value) == 'Unknown node %s' % fake_node

    def test_exception_raised_for_unknown_test(self):
        with pytest.raises(Exception) as e:
            JinjaToJS(template_string='{% if foo is someunknowntest %}{% endif %}')
        assert str(e.value) == 'Unsupported test: someunknowntest'

    def test_exception_raised_for_unknown_filter(self):
        with pytest.raises(Exception) as e:
            JinjaToJS(template_string='{{ something|somefilter() }}')
        assert str(e.value) == 'Unsupported filter: somefilter'

    def test_super_called_outside_of_block(self):
        with pytest.raises(Exception) as e:
            JinjaToJS(template_string='{% block foo %}{{ super() }}{% endblock %}')
        assert str(e.value) == 'super() called outside of a block with a parent.'

    def test_call_node(self):
        JinjaToJS(template_string='{{ foo() }}').get_output() == '<%- context.foo(); %>'
        JinjaToJS(template_string='{{ foo(1,2,3) }}').get_output() == '<%- context.foo(1,2,3); %>'
        JinjaToJS(template_string='{{ foo(a,b,c) }}').get_output() == '<%- context.foo(a,b,c); %>'
        JinjaToJS(template_string='{{ foo.bar() }}').get_output() == '<%- context.foo.bar(); %>'

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
                       ),
                       somefunction=lambda *args: 'hello')

    def test_iteration_iteritems(self):
        if hasattr(dict, 'iteritems'):
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
        self._run_test('filters/safe.jinja', foo='&lt;div&gt;', obj=dict(key='&lt;div&gt;'))

    def test_capitalize_filter(self):
        self._run_test('filters/capitalize.jinja', first_name='jon')

    def test_abs_filter(self):
        self._run_test('filters/abs.jinja', some_number=5, some_float=5.5)

    def test_batch_filter(self):
        self._run_test('filters/batch.jinja', items=[
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'
        ])

    def test_default_filter(self):
        self._run_test('filters/default.jinja', falsey_value='')

    def test_first_filter(self):
        self._run_test('filters/first.jinja', list_of_things=[1, 2, 3])

    def test_last_filter(self):
        self._run_test('filters/last.jinja', list_of_things=[1, 2, 3])

    def test_int_filter(self):
        self._run_test('filters/int.jinja', a_valid_number='5', not_a_valid_number='cats')

    def test_attr_filter(self):
        class Foo(object):
            def __init__(self):
                self.my_key = 'my value'

        self._run_test('filters/attr.jinja', obj=Foo(), obj_key='my_key')

    def test_length_filter(self):
        self._run_test('filters/length.jinja', obj=dict(a=1, b=2, c=3), list=[1, 2, 3])

    def test_lower_filter(self):
        self._run_test('filters/lower.jinja', shouty_text='I AM SHOUTING')

    def test_slice_filter(self):
        self._run_test('filters/slice.jinja', items=[
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'
        ])

    def test_title_filter(self):
        self._run_test('filters/title.jinja', some_text='testing is fun')

    def test_trim_filter(self):
        self._run_test('filters/trim.jinja', some_text='   so much whitespace   ')

    def test_upper_filter(self):
        self._run_test('filters/upper.jinja', some_text='make me shouty')

    def test_truncate_filter(self):
        self._run_test('filters/truncate.jinja',
                       some_text='I am far too long and need to be truncated.')

    def test_conditions(self):
        self._run_test('conditions.jinja',
                       foo=False, bar=6, baz=3,
                       person='jimmy', fizz=5, buzz=5)

    def test_loop_helpers(self):
        self._run_test('loop_helpers.jinja', things=[1, 2, 3, 4, 5, 6])

    def test_tests(self):
        self._run_test('tests.jinja',
                       age=30, fn=lambda x: x, not_a_fn=None, i_am_none=None,
                       upper_str='HELLO', lower_str='hello',
                       a_mapping=dict(key='value'))

    def test_truthy_falsey_values(self):
        self._run_test('truthy_falsey_values.jinja',
                       non_empty_array=[1, 2, 3],
                       empty_array=[],
                       empty_object={},
                       non_empty_object=dict(inner_key='one', inner_obj=dict(inner_inner_key=5)),
                       empty_string='',
                       non_empty_string='hello',
                       boolean_true=True,
                       boolean_false=False)

    def test_comparisons(self):
        self._run_test('comparisons.jinja',
                       list_a=[1, 2, 3],
                       list_b=[1, 2, 3],
                       list_c=[2, 3, 4],
                       dict_a=dict(one='one'),
                       dict_b=dict(one='one'),
                       dict_c=dict(two='two'),
                       number_1=1,
                       number_2=2,
                       letter_a='a',
                       letter_b='b')

    def test_include(self):
        self._run_test('include.jinja',
                       additional=['includes/name.jinja'],
                       the_beatles=['John', 'Paul', 'George', 'Ringo'])

    def test_math(self):
        self._run_test('math.jinja')

    def test_extends(self):
        self._run_test('extends.jinja')

    def test_logic(self):
        self._run_test('logic.jinja', foo=True, bar=True, baz=True)
        self._run_test('logic.jinja', foo=True, bar=True, baz=False)
        self._run_test('logic.jinja', foo=True, bar=False, baz=True)
        self._run_test('logic.jinja', foo=False, bar=True, baz=True)
        self._run_test('logic.jinja', foo=False, bar=False, baz=False)

    def test_escape(self):
        self._run_test('escape.jinja',
                       some_user_input='<script>alert("hello");</script><p class="foo"></p>')

    def test_function_calls(self):
        self._run_test('function_calls.jinja', foo=lambda: 'hello')

    def _run_test(self, name, additional=None, **kwargs):

        # first we'll render the jinja template
        jinja_result = self.env.get_template(name).render(**kwargs).strip()

        # create the main template
        path = self._compile_js_template(name)
        template_args = [path]

        # create a temp file containing the data
        data_file_path = self._write_to_temp_file(json.dumps(kwargs, cls=Encoder))

        # if additional template are required e.g. for includes then create those too
        if additional:
            for n in additional:
                self._compile_js_template(n)

        # get the result of rendering the javascript template
        try:
            js_result = check_output(
                ['node',
                 self.NODE_SCRIPT_PATH]
                + template_args +
                [data_file_path]
            )
        except Exception as e:
            raise e

        jinja_result = jinja_result.strip()
        js_result = js_result.strip()

        if isinstance(js_result, bytes):
            js_result = js_result.decode('utf8')

        # check the jinja result and the javascript result are the same
        assert jinja_result == js_result

    def _compile_js_template(self, name):
        js_module = JinjaToJS(
            self.env,
            template_name=name,
            js_module_format='commonjs',
            include_prefix=self.temp_dir + '/',
            runtime_path=abspath('jinja-to-js-runtime.js')
        ).get_output()

        target = self.temp_dir + '/' + os.path.splitext(name)[0] + '.js'

        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))

        with open(target, 'w') as f:
            f.write(js_module)

        return target

    def _write_to_temp_file(self, data):
        fd, file_path = tempfile.mkstemp()
        f = os.fdopen(fd, 'w')
        f.write(data)
        f.flush()
        os.fsync(fd)
        f.close()
        return file_path
