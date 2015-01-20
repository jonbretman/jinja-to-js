import contextlib

from cStringIO import StringIO
import json
from jinja2 import nodes, Environment
from jinja2.nodes import Call, Getattr


def compile_string(template_str, environment=None):
    """
    Compiles a Jinja template string into an Underscore template.
    Useful for quick testing on the command line.
    """

    if environment is None:
        environment = Environment(extensions=['jinja2.ext.with_'])

    return JinjaToJS(environment=environment, template_string=template_str).get_output()


OPTION_USE_OK_WRAPPER = 'use_ok_wrapper'

INTERPOLATION_START = '<%- '
INTERPOLATION_END = ' %>'
INTERPOLATION_SAFE_START = '<%= '
EXECUTE_START = '<% '
EXECUTE_END = ' %>'

CONTEXT_NAME = 'context'

OPERANDS = {
    'eq': '',  # handled by _.isEqual
    'ne': '',  # handled by _.isEqual
    'lt': ' < ',
    'gt': ' > ',
    'lteq': ' <= ',
    'gteq': ' >= '
}

# this function emulates Pythons boolean evaluation e.g. an empty list or object is false
TRUTHY_HELPER = """
%s
function __ok(o) {
    var toString = Object.prototype.toString;
    return !o ? false : toString.call(o).match(/\[object (Array|Object)\]/) ? !_.isEmpty(o) : !!o;
}
%s
""" % (EXECUTE_START, EXECUTE_END)

DICT_ITER_METHODS = (
    dict.iteritems.__name__,
    dict.items.__name__,
    dict.values.__name__,
    dict.keys.__name__
)

STATE_DEFAULT = 0
STATE_EXECUTING = 1
STATE_INTERPOLATING = 2

LOOP_HELPER_INDEX = 'index'
LOOP_HELPER_INDEX_0 = 'index0'
LOOP_HELPER_FIRST = 'first'
LOOP_HELPER_LAST = 'last'
LOOP_HELPER_LENGTH = 'length'
LOOP_HELPERS = (
    LOOP_HELPER_INDEX,
    LOOP_HELPER_INDEX_0,
    LOOP_HELPER_FIRST,
    LOOP_HELPER_LAST,
    LOOP_HELPER_LENGTH
)


@contextlib.contextmanager
def option(kwargs, key, value=True):
    old_value = kwargs.get(key)
    kwargs[key] = value
    yield
    kwargs[key] = old_value


def is_method_call(node, method_name):
    if not isinstance(node, Call):
        return False

    if not isinstance(node.node, Getattr):
        return False

    method = node.node.attr

    if isinstance(method_name, (list, tuple)):
        return method in method_name

    return method == method_name


def is_loop_helper(node):
    return hasattr(node, 'node') and isinstance(node.node, nodes.Name) and node.node.name == 'loop'


def temp_var_names_generator():
    x = 0
    while True:
        yield '__$%s' % x
        x += 1


def noop():
    pass


class JinjaToJS(object):

    def __init__(self, environment, template_name=None,
                 template_string=None, include_fn_name='context.include'):
        self.environment = environment
        self.output = StringIO()
        self.stored_names = set()
        self.temp_var_names = temp_var_names_generator()
        self.include_fn_name = include_fn_name
        self.state = STATE_DEFAULT

        if template_name is not None:
            template_string, _, _ = environment.loader.get_source(environment, template_name)

        if not template_string:
            raise ValueError('Either a template_name or template_string must be provided.')

        ast = environment.parse(template_string)

        for node in ast.body:
            self._process_node(node)

    def get_output(self):
        return self.output.getvalue()

    def _execute_start(self):
        if self.state == STATE_DEFAULT:
            self.output.write(EXECUTE_START)
            self.state = STATE_EXECUTING
            return self._execute_end
        return noop

    def _execute_end(self):
        self.output.write(EXECUTE_END)
        self.state = STATE_DEFAULT

    def _interpolate_start(self):
        if self.state == STATE_DEFAULT:
            self.output.write(INTERPOLATION_START)
            self.state = STATE_INTERPOLATING
            return self._interpolate_end
        return noop

    def _interpolate_safe_start(self):
        if self.state == STATE_DEFAULT:
            self.output.write(INTERPOLATION_SAFE_START)
            self.state = STATE_INTERPOLATING
            return self._interpolate_end
        return noop

    def _interpolate_end(self):
        self.output.write(INTERPOLATION_END)
        self.state = STATE_DEFAULT

    def _process_node(self, node, **kwargs):
        node_name = node.__class__.__name__.lower()
        handler = getattr(self, '_process_' + node_name, None)
        if callable(handler):
            handler(node, **kwargs)
        else:
            raise Exception('Unknown node %s' % node)

    def _process_output(self, node, **kwargs):
        for n in node.nodes:
            self._process_node(n, **kwargs)

    def _process_templatedata(self, node, **_):
        self.output.write(node.data)

    def _process_name(self, node, **kwargs):

        close_interpolation = self._interpolate_start()

        if kwargs.get(OPTION_USE_OK_WRAPPER):
            self._add_truthy_helper()
            self.output.write('__ok(')

        if node.name not in self.stored_names and node.ctx != 'store':
            self.output.write(CONTEXT_NAME)
            self.output.write('.')

        if node.ctx == 'store':
            self.stored_names.add(node.name)

        self.output.write(node.name)

        if kwargs.get(OPTION_USE_OK_WRAPPER):
            self.output.write(')')

        close_interpolation()

    def _process_getattr(self, node, **kwargs):

        close_interpolation = self._interpolate_start()

        if is_loop_helper(node):
            self._process_loop_helper(node, **kwargs)
        else:
            self._process_node(node.node, **kwargs)
            self.output.write('.')
            self.output.write(node.attr)

        close_interpolation()

    def _process_getitem(self, node, **kwargs):

        close_interpolation = self._interpolate_start()

        if is_loop_helper(node):
            self._process_loop_helper(node, **kwargs)
        else:
            self._process_node(node.node, **kwargs)
            self.output.write('[')
            self._process_node(node.arg, **kwargs)
            self.output.write(']')

        close_interpolation()

    def _process_for(self, node, **kwargs):
        # since a for loop can introduce new names into the context
        # we need to remember the ones that existed outside the loop
        previous_stored_names = self.stored_names.copy()

        execute_end = self._execute_start()
        self.output.write('_.each(')

        if is_method_call(node.iter, dict.keys.__name__):
            self.output.write('_.keys(')

        self._process_node(node.iter, **kwargs)

        if is_method_call(node.iter, dict.keys.__name__):
            self.output.write(')')

        self.output.write(',')
        self.output.write('function')
        self.output.write('(')

        # javascript iterations put the value first, then the key
        if isinstance(node.target, nodes.Tuple):
            tmp = node.target.items[0]
            node.target.items[0] = node.target.items[1]
            node.target.items[1] = tmp

        self._process_node(node.target, **kwargs)

        self.output.write(')')
        self.output.write('{')

        if node.test:
            self.output.write('if (!(')
            self._process_node(node.test, **kwargs)
            self.output.write(')) { return; }')

        execute_end()

        assigns = node.target.items if isinstance(node.target, nodes.Tuple) else [node.target]

        with self._scoped_variables(assigns, **kwargs):
            for n in node.body:
                self._process_node(n, **kwargs)

        execute_end = self._execute_start()
        self.output.write('}')
        self.output.write(')')
        self.output.write(';')
        execute_end()

        # restore the stored names
        self.stored_names = previous_stored_names

    def _process_if(self, node, execute_end=None, **kwargs):
        # condition
        execute_end = execute_end or self._execute_start()
        self.output.write('if')
        self.output.write('(')

        with option(kwargs, OPTION_USE_OK_WRAPPER):
            self._process_node(node.test, **kwargs)

        self.output.write(')')
        self.output.write('{')
        execute_end()

        # body
        for n in node.body:
            self._process_node(n, **kwargs)

        # no else
        if not node.else_:
            execute_end = self._execute_start()
            self.output.write('}')
            execute_end()

        # with an else
        else:
            execute_end = self._execute_start()
            self.output.write('}')
            self.output.write(' else ')

            # else if
            if isinstance(node.else_[0], nodes.If):
                for n in node.else_:
                    self._process_node(n, execute_end=execute_end, **kwargs)
            else:
                self.output.write('{')
                execute_end()
                for n in node.else_:
                    self._process_node(n, **kwargs)
                execute_end = self._execute_start()
                self.output.write('}')
                execute_end()

    def _process_not(self, node, **kwargs):
        self.output.write('!')
        self._process_node(node.node, **kwargs)

    def _process_or(self, node, **kwargs):
        self._process_node(node.left, **kwargs)
        self.output.write(' || ')
        self._process_node(node.right, **kwargs)

    def _process_and(self, node, **kwargs):
        self._process_node(node.left, **kwargs)
        self.output.write(' && ')
        self._process_node(node.right, **kwargs)

    def _process_tuple(self, node, **kwargs):
        for i, item in enumerate(node.items):
            self._process_node(item, **kwargs)
            if i < len(node.items) - 1:
                self.output.write(',')

    def _process_call(self, node, **kwargs):
        if is_method_call(node, DICT_ITER_METHODS):
            self._process_node(node.node.node, **kwargs)
        else:
            raise Exception('Usage of call with unknown method %s: %s' % (node.node.attr, node))

    def _process_filter(self, node, **kwargs):
        if node.name == 'safe':
            interpolate_close = self._interpolate_safe_start()
            self._process_node(node.node, **kwargs)
            interpolate_close()
        else:
            raise Exception('Unsupported filter %s', node)

    def _process_assign(self, node, **kwargs):
        execute_end = self._execute_start()
        self.output.write('var ')
        self._process_node(node.target, **kwargs)
        self.output.write(' = ')
        self._process_node(node.node, **kwargs)
        self.output.write(';')
        execute_end()

    def _process_scope(self, node, **kwargs):

        # keep a copy of the stored names before the scope
        previous_stored_names = self.stored_names.copy()

        assigns = [x for x in node.body if isinstance(x, nodes.Assign)]
        node.body = [x for x in node.body if not isinstance(x, nodes.Assign)]

        execute_end = self._execute_start()
        self.output.write('(function () {')
        execute_end()

        with self._scoped_variables(assigns, **kwargs):
            for node in node.body:
                self._process_node(node, **kwargs)

        execute_end = self._execute_start()
        self.output.write('})();')
        execute_end()

        # restore previous stored names
        self.stored_names = previous_stored_names

    def _process_compare(self, node, **kwargs):
        operand = node.ops[0].op
        use_is_equal = operand in ('eq', 'ne')

        with option(kwargs, OPTION_USE_OK_WRAPPER, False):

            if use_is_equal:
                if operand == 'ne':
                    self.output.write('!')
                self.output.write('_.isEqual(')

            self._process_node(node.expr, **kwargs)

            if use_is_equal:
                self.output.write(',')

            for n in node.ops:
                self._process_node(n, **kwargs)

            if use_is_equal:
                self.output.write(')')

    def _process_operand(self, node, **kwargs):
        operand = OPERANDS.get(node.op)
        if operand is None:
            raise Exception('Unknown operand %s' % node.op)
        self.output.write(operand)
        self._process_node(node.expr, **kwargs)

    def _process_const(self, node, **_):
        close_interpolation = self._interpolate_start()
        self.output.write(json.dumps(node.value))
        close_interpolation()

    def _process_list(self, node, **kwargs):
        self.output.write('[')
        for i, item in enumerate(node.items):
            self._process_node(item, **kwargs)
            if i < len(node.items) - 1:
                self.output.write(',')
        self.output.write(']')

    def _process_test(self, node, **kwargs):
        with option(kwargs, OPTION_USE_OK_WRAPPER, False):
            if node.name in ('defined', 'undefined'):
                self.output.write('(')
                self.output.write('typeof ')
                self._process_node(node.node, **kwargs)
                self.output.write(' !== ' if node.name == 'defined' else ' === ')
                self.output.write('"undefined"')
                self.output.write(')')
            else:
                raise Exception('Unsupported test %s' % node.name)

    def _process_include(self, node, **kwargs):
        self.output.write(INTERPOLATION_SAFE_START)
        self.state = STATE_INTERPOLATING
        self.output.write(self.include_fn_name)
        self.output.write('(')
        self._process_node(node.template, **kwargs)
        self.output.write(')')
        self.output.write('(')
        self.output.write(CONTEXT_NAME)
        self.output.write(')')
        self.output.write(INTERPOLATION_END)
        self.state = STATE_DEFAULT

    def _process_add(self, node, **kwargs):
        self._process_math(node, math_operator=' + ', **kwargs)

    def _process_sub(self, node, **kwargs):
        self._process_math(node, math_operator=' - ', **kwargs)

    def _process_div(self, node, **kwargs):
        self._process_math(node, math_operator=' / ', **kwargs)

    def _process_floordiv(self, node, **kwargs):
        self._process_math(node, math_operator=' / ', function='Math.floor', **kwargs)

    def _process_mul(self, node, **kwargs):
        self._process_math(node, math_operator=' * ', **kwargs)

    def _process_mod(self, node, **kwargs):
        self._process_math(node, math_operator=' % ', **kwargs)

    def _process_math(self, node, math_operator=None, function=None, **kwargs):

        interpolate_close = self._interpolate_start()

        if function:
            self.output.write(function)
            self.output.write('(')

        self._process_node(node.left, **kwargs)
        self.output.write(math_operator)
        self._process_node(node.right, **kwargs)

        if function:
            self.output.write(')')

        interpolate_close()

    def _process_loop_helper(self, node, **kwargs):
        if node.attr == LOOP_HELPER_INDEX:
            self.output.write('(arguments[1] + 1)')
        elif node.attr == LOOP_HELPER_INDEX_0:
            self.output.write('arguments[1]')
        elif node.attr == LOOP_HELPER_FIRST:
            self.output.write('(arguments[1] == 0)')
        elif node.attr == LOOP_HELPER_LAST:
            self.output.write('(arguments[1] == arguments[2].length - 1)')
        elif node.attr == LOOP_HELPER_LENGTH:
            self.output.write('arguments[2].length')

    def _add_truthy_helper(self):
        if getattr(self, '_truthy_helper_added', False):
            return

        output = StringIO()
        output.write(TRUTHY_HELPER)
        output.write(self.output.getvalue())
        self.output = output
        setattr(self, '_truthy_helper_added', True)

    @contextlib.contextmanager
    def _scoped_variables(self, nodes_list, **kwargs):
        tmp_vars = []
        for node in nodes_list:

            is_assign_node = isinstance(node, nodes.Assign)
            name = node.target.name if is_assign_node else node.name

            # create a temp variable name
            tmp_var = self.temp_var_names.next()

            # save previous context value
            execute_end = self._execute_start()
            self.output.write('var ')
            self.output.write(tmp_var)
            self.output.write(' = ')
            self.output.write(CONTEXT_NAME)
            self.output.write('.')
            self.output.write(name)
            self.output.write(';')

            # add new value to context
            self.output.write(CONTEXT_NAME)
            self.output.write('.')
            self.output.write(name)
            self.output.write(' = ')

            if is_assign_node:
                self._process_node(node.node, **kwargs)
            else:
                self.output.write(node.name)

            self.output.write(';')
            execute_end()

            tmp_vars.append((tmp_var, name))

        yield

        # restore context
        for tmp_var, name in tmp_vars:
            execute_end = self._execute_start()
            self.output.write(CONTEXT_NAME)
            self.output.write('.')
            self.output.write(name)
            self.output.write(' = ')
            self.output.write(tmp_var)
            self.output.write(';')
            execute_end()
