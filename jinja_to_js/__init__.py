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


OPTION_INSIDE_IF = 'inside_if'
OPTION_NO_INTERPOLATE = 'no_interpolate'
OPTION_INTERPOLATE_SAFE = 'interpolate_safe'
OPTION_USE_OK_WRAPPER = 'use_ok_wrapper'

INTERPOLATION_START = '<%- '
INTERPOLATION_END = ' %>'
INTERPOLATION_SAFE_START = '<%= '
PROPERTY_ACCESSOR = '.'
EXECUTE_START = '<% '
EXECUTE_END = ' %>'
BLOCK_OPEN = '{'
BLOCK_CLOSE = '}'
ARRAY_OPEN = '['
ARRAY_CLOSE = ']'
COMMA = ', '
FUNCTION = 'function'
IIFE_START = '(function () {'
IIFE_END = '})();'
PAREN_START = ' ('
PAREN_END = ') '
EACH_START = '_.each('
KEYS_START = '_.keys('
IS_EQUAL_START = '_.isEqual('
OK_FUNCTION_START = '__ok('
VAR = 'var '
TERMINATOR = ';'
IF = 'if'
ELSE = ' else '
NOT = '!'
OR = ' || '
AND = ' && '
ASSIGN = ' = '
NOT_EQUAL = ' !== '
EQUAL = ' === '
TYPEOF = 'typeof '
STR_UNDEFINED = '"undefined"'
CONTEXT_NAME = 'context'
OPERANDS = {
    'eq': '',
    'ne': '',
    'lt': ' < ',
    'gt': ' > ',
    'lteq': ' <= ',
    'gteq': ' >= '
}

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


class JinjaToJS(object):

    def __init__(self, environment, template_name=None, template_string=None):
        self.environment = environment
        self.output = StringIO()
        self.stored_names = set()
        self.temp_var_names = temp_var_names_generator()

        if template_name is not None:
            template_string, _, _ = environment.loader.get_source(environment, template_name)

        if not template_string:
            raise ValueError('Either a template_name or template_string must be provided.')

        ast = environment.parse(template_string)

        for node in ast.body:
            self._process_node(node)

    def get_output(self):
        return self.output.getvalue()

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
        if not kwargs.get(OPTION_NO_INTERPOLATE):
            if kwargs.get(OPTION_INTERPOLATE_SAFE):
                self.output.write(INTERPOLATION_SAFE_START)
            else:
                self.output.write(INTERPOLATION_START)

        if kwargs.get(OPTION_USE_OK_WRAPPER):
            self._add_truthy_helper()
            self.output.write(OK_FUNCTION_START)

        if node.name not in self.stored_names and node.ctx != 'store':
            self.output.write(CONTEXT_NAME)
            self.output.write(PROPERTY_ACCESSOR)

        if node.ctx == 'store':
            self.stored_names.add(node.name)

        self.output.write(node.name)

        if kwargs.get(OPTION_USE_OK_WRAPPER):
            self.output.write(PAREN_END)

        if not kwargs.get(OPTION_NO_INTERPOLATE):
            self.output.write(INTERPOLATION_END)

    def _process_getattr(self, node, **kwargs):
        if not kwargs.get(OPTION_NO_INTERPOLATE):
            self.output.write(INTERPOLATION_START)

        if is_loop_helper(node):
            self._process_loop_helper(node, **kwargs)
        else:
            with option(kwargs, OPTION_NO_INTERPOLATE):
                self._process_node(node.node, **kwargs)
                self.output.write(PROPERTY_ACCESSOR)
                self.output.write(node.attr)

        if not kwargs.get(OPTION_NO_INTERPOLATE):
            self.output.write(INTERPOLATION_END)

    def _process_for(self, node, **kwargs):
        # since a for loop can introduce new names into the context
        # we need to remember the ones that existed outside the loop
        previous_stored_names = self.stored_names.copy()

        self.output.write(EXECUTE_START)
        self.output.write(EACH_START)

        if is_method_call(node.iter, dict.keys.__name__):
            self.output.write(KEYS_START)

        with option(kwargs, OPTION_NO_INTERPOLATE):
            self._process_node(node.iter, **kwargs)

        if is_method_call(node.iter, dict.keys.__name__):
            self.output.write(PAREN_END)

        self.output.write(COMMA)
        self.output.write(FUNCTION)
        self.output.write(PAREN_START)

        # javascript iterations put the value first, then the key
        if isinstance(node.target, nodes.Tuple):
            tmp = node.target.items[0]
            node.target.items[0] = node.target.items[1]
            node.target.items[1] = tmp

        with option(kwargs, OPTION_NO_INTERPOLATE):
            self._process_node(node.target, **kwargs)

        self.output.write(PAREN_END)
        self.output.write(BLOCK_OPEN)
        self.output.write(EXECUTE_END)

        assigns = node.target.items if isinstance(node.target, nodes.Tuple) else [node.target]

        with self._scoped_variables(assigns, **kwargs):
            for n in node.body:
                self._process_node(n, **kwargs)

        self.output.write(EXECUTE_START)
        self.output.write(BLOCK_CLOSE)
        self.output.write(PAREN_END)
        self.output.write(TERMINATOR)
        self.output.write(EXECUTE_END)

        # restore the stored names
        self.stored_names = previous_stored_names

    def _process_if(self, node, **kwargs):
        # condition
        with option(kwargs, OPTION_NO_INTERPOLATE):
            if not kwargs.get(OPTION_INSIDE_IF):
                self.output.write(EXECUTE_START)
            self.output.write(IF)
            self.output.write(PAREN_START)

            with option(kwargs, OPTION_USE_OK_WRAPPER):
                self._process_node(node.test, **kwargs)

            self.output.write(PAREN_END)
            self.output.write(BLOCK_OPEN)
            self.output.write(EXECUTE_END)

        # body
        for n in node.body:
            self._process_node(n, **kwargs)

        # no else
        if not node.else_:
            self.output.write(EXECUTE_START)
            self.output.write(BLOCK_CLOSE)
            self.output.write(EXECUTE_END)

        # with an else
        else:
            self.output.write(EXECUTE_START)
            self.output.write(BLOCK_CLOSE)
            self.output.write(ELSE)

            # else if
            if isinstance(node.else_[0], nodes.If):
                with option(kwargs, OPTION_INSIDE_IF):
                    for n in node.else_:
                        self._process_node(n, **kwargs)
            else:
                self.output.write(BLOCK_OPEN)
                self.output.write(EXECUTE_END)
                for n in node.else_:
                    self._process_node(n, **kwargs)
                self.output.write(EXECUTE_START)
                self.output.write(BLOCK_CLOSE)
                self.output.write(EXECUTE_END)

    def _process_not(self, node, **kwargs):
        self.output.write(NOT)
        self._process_node(node.node, **kwargs)

    def _process_or(self, node, **kwargs):
        self._process_node(node.left, **kwargs)
        self.output.write(OR)
        self._process_node(node.right, **kwargs)

    def _process_and(self, node, **kwargs):
        self._process_node(node.left, **kwargs)
        self.output.write(AND)
        self._process_node(node.right, **kwargs)

    def _process_tuple(self, node, **kwargs):
        for i, item in enumerate(node.items):
            self._process_node(item, **kwargs)
            if i < len(node.items) - 1:
                self.output.write(COMMA)

    def _process_call(self, node, **kwargs):
        if is_method_call(node, DICT_ITER_METHODS):
            self._process_node(node.node.node, **kwargs)
        else:
            raise Exception('Usage of call with unknown method %s: %s' % (node.node.attr, node))

    def _process_filter(self, node, **kwargs):
        if node.name == 'safe':
            with option(kwargs, OPTION_INTERPOLATE_SAFE):
                self._process_node(node.node, **kwargs)
        else:
            raise Exception('Unsupported filter %s', node)

    def _process_assign(self, node, **kwargs):
        self.output.write(EXECUTE_START)
        self.output.write(VAR)

        with option(kwargs, OPTION_NO_INTERPOLATE):
            self._process_node(node.target, **kwargs)

        self.output.write(ASSIGN)

        with option(kwargs, OPTION_NO_INTERPOLATE):
            self._process_node(node.node, **kwargs)

        self.output.write(TERMINATOR)
        self.output.write(EXECUTE_END)

    def _process_scope(self, node, **kwargs):

        # keep a copy of the stored names before the scope
        previous_stored_names = self.stored_names.copy()

        assigns = [x for x in node.body if isinstance(x, nodes.Assign)]
        node.body = [x for x in node.body if not isinstance(x, nodes.Assign)]

        self.output.write(EXECUTE_START)
        self.output.write(IIFE_START)
        self.output.write(EXECUTE_END)

        with self._scoped_variables(assigns, **kwargs):
            for node in node.body:
                self._process_node(node, **kwargs)

        self.output.write(EXECUTE_START)
        self.output.write(IIFE_END)
        self.output.write(EXECUTE_END)

        # restore previous stored names
        self.stored_names = previous_stored_names

    def _process_compare(self, node, **kwargs):
        operand = node.ops[0].op
        use_is_equal = operand in ('eq', 'ne')

        with option(kwargs, OPTION_USE_OK_WRAPPER, False):

            if use_is_equal:
                if operand == 'ne':
                    self.output.write(NOT)
                self.output.write(IS_EQUAL_START)

            self._process_node(node.expr, **kwargs)

            if use_is_equal:
                self.output.write(COMMA)

            for n in node.ops:
                self._process_node(n, **kwargs)

            if use_is_equal:
                self.output.write(PAREN_END)

    def _process_operand(self, node, **kwargs):
        operand = OPERANDS.get(node.op)
        if operand is None:
            raise Exception('Unknown operand %s' % node.op)
        self.output.write(operand)
        self._process_node(node.expr, **kwargs)

    def _process_const(self, node, **_):
        self.output.write(json.dumps(node.value))

    def _process_list(self, node, **kwargs):
        self.output.write(ARRAY_OPEN)
        for i, item in enumerate(node.items):
            self._process_node(item, **kwargs)
            if i < len(node.items) - 1:
                self.output.write(COMMA)
        self.output.write(ARRAY_CLOSE)

    def _process_test(self, node, **kwargs):
        with option(kwargs, OPTION_USE_OK_WRAPPER, False):
            if node.name in ('defined', 'undefined'):
                self.output.write(PAREN_START)
                self.output.write(TYPEOF)
                with option(kwargs, OPTION_NO_INTERPOLATE):
                    self._process_node(node.node, **kwargs)
                self.output.write(NOT_EQUAL if node.name == 'defined' else EQUAL)
                self.output.write(STR_UNDEFINED)
                self.output.write(PAREN_END)
            else:
                raise Exception('Unsupported test %s' % node.name)

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
            self.output.write(EXECUTE_START)
            self.output.write(VAR)
            self.output.write(tmp_var)
            self.output.write(ASSIGN)
            self.output.write(CONTEXT_NAME)
            self.output.write(PROPERTY_ACCESSOR)
            self.output.write(name)
            self.output.write(TERMINATOR)

            # add new value to context
            self.output.write(CONTEXT_NAME)
            self.output.write(PROPERTY_ACCESSOR)
            self.output.write(name)
            self.output.write(ASSIGN)

            if is_assign_node:
                with option(kwargs, OPTION_NO_INTERPOLATE):
                    self._process_node(node.node, **kwargs)
            else:
                self.output.write(node.name)

            self.output.write(TERMINATOR)
            self.output.write(EXECUTE_END)

            tmp_vars.append((tmp_var, name))

        yield

        # restore context
        for tmp_var, name in tmp_vars:
            self.output.write(EXECUTE_START)
            self.output.write(CONTEXT_NAME)
            self.output.write(PROPERTY_ACCESSOR)
            self.output.write(name)
            self.output.write(ASSIGN)
            self.output.write(tmp_var)
            self.output.write(TERMINATOR)
            self.output.write(EXECUTE_END)
