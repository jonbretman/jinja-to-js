import contextlib

from cStringIO import StringIO
import json
from jinja2 import nodes, Environment


def compile_string(template_str, environment=None):
    """
    Compiles a Jinja template string into an Underscore template.
    Useful for quick testing on the command line.
    """

    if environment is None:
        environment = Environment(extensions=['jinja2.ext.with_'])

    return JinjaToJS(environment=environment, template_string=template_str).get_output()


OPERANDS = {
    'eq': '',  # handled by _.isEqual
    'ne': '',  # handled by _.isEqual
    'lt': ' < ',
    'gt': ' > ',
    'lteq': ' <= ',
    'gteq': ' >= '
}

# this function emulates Pythons boolean evaluation e.g. an empty list or object is false
PYTHON_BOOL_EVAL_FUNCTION = """
<%
function __ok(o) {
    var toString = Object.prototype.toString;
    return !o ? false : toString.call(o).match(/\[object (Array|Object)\]/) ? !_.isEmpty(o) : !!o;
}
%>
"""

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


class ExtendsException(Exception):
    """
    Raised when an {% extends %} is encountered. At this point the parent template is
    loaded and all blocks defined in the current template passed to it.
    """
    pass


@contextlib.contextmanager
def option(current_kwargs, **kwargs):
    """
    Context manager for temporarily setting a keyword argument and
    then restoring it to whatever it was before.
    """

    tmp_kwargs = {key: current_kwargs.get(key) for key, value in kwargs.items()}
    current_kwargs.update(kwargs)
    yield
    current_kwargs.update(tmp_kwargs)


def is_method_call(node, method_name):
    """
    Returns True if `node` is a method call for `method_name`. `method_name`
    can be either a string or an iterable of strings.
    """

    if not isinstance(node, nodes.Call):
        return False

    if isinstance(node.node, nodes.Getattr):
        # e.g. foo.bar()
        method = node.node.attr

    elif isinstance(node.node, nodes.Name):
        # e.g. bar()
        method = node.node.name

    else:
        return False

    if isinstance(method_name, (list, tuple)):
        return method in method_name

    return method == method_name


def is_loop_helper(node):
    """
    Returns True is node is a loop helper e.g. {{ loop.index }} or {{ loop.first }}
    """
    return hasattr(node, 'node') and isinstance(node.node, nodes.Name) and node.node.name == 'loop'


def temp_var_names_generator():
    x = 0
    while True:
        yield '__$%s' % x
        x += 1


class JinjaToJS(object):

    def __init__(self, environment, template_name=None,
                 template_string=None, include_fn_name='context.include',
                 content_name='context', child_blocks=None):
        self.environment = environment
        self.output = StringIO()
        self.stored_names = set()
        self.temp_var_names = temp_var_names_generator()
        self.include_fn_name = include_fn_name
        self.context_name = content_name
        self.state = STATE_DEFAULT
        self.child_blocks = child_blocks or {}

        if template_name is not None:
            template_string, _, _ = environment.loader.get_source(environment, template_name)

        if not template_string:
            raise ValueError('Either a template_name or template_string must be provided.')

        self.ast = environment.parse(template_string)

        try:
            for node in self.ast.body:
                self._process_node(node)
        except ExtendsException:
            pass

    def get_output(self):
        return self.output.getvalue()

    def _process_node(self, node, **kwargs):
        node_name = node.__class__.__name__.lower()
        handler = getattr(self, '_process_' + node_name, None)
        if callable(handler):
            handler(node, **kwargs)
        else:
            raise Exception('Unknown node %s' % node)

    def _process_extends(self, node, **kwargs):
        """
        Processes an extends block e.g. `{% extends "some/template.jinja" %}`
        """

        # find all the blocks in this template
        for b in self.ast.find_all(nodes.Block):

            # if not already in `child_blocks` then this is the first time a
            # block with this name has been encountered.
            if b.name not in self.child_blocks:
                self.child_blocks[b.name] = b
            else:

                # otherwise we have seen this block before, so we need to find the last
                # super_block and add the block from this template to the end.
                block = self.child_blocks[b.name]
                while hasattr(block, 'super_block'):
                    block = block.super_block
                block.super_block = b

        # load the parent template
        parent_template = JinjaToJS(environment=self.environment,
                                    template_name=node.template.value,
                                    include_fn_name=self.include_fn_name,
                                    child_blocks=self.child_blocks)

        # add the parent templates output to the current output
        self.output.write(parent_template.get_output())

        # Raise an exception so we stop parsing this template
        raise ExtendsException

    def _process_block(self, node, child_block=None, **kwargs):
        """
        Processes a block e.g. `{% block my_block %}{% endblock %}`
        """

        if not child_block:
            child_block = self.child_blocks.get(node.name)

        if not child_block:
            for n in node.body:
                self._process_node(n, **kwargs)
        else:
            if not hasattr(child_block, 'super_block'):
                child_block.super_block = node
            for n in child_block.body:
                self._process_node(n, super_block=child_block.super_block, **kwargs)

    def _process_output(self, node, **kwargs):
        """
        Processes an output node, which will contain things like `Name` and `TemplateData` nodes.
        """
        for n in node.nodes:
            self._process_node(n, **kwargs)

    def _process_templatedata(self, node, **_):
        """
        Processes a `TemplateData` node, this is just a bit of as-is text
        to be written to the output.
        """
        self.output.write(node.data)

    def _process_name(self, node, use_python_bool_wrapper=False, **kwargs):
        """
        Processes a `Name` node. Some examples of `Name` nodes:
            {{ foo }} -> 'foo' is a Name
            {% if foo }} -> 'foo' is a Name
        """

        with self._interpolation():
            if use_python_bool_wrapper:
                self._add_python_bool_function()
                self.output.write('__ok(')

            if node.name not in self.stored_names and node.ctx != 'store':
                self.output.write(self.context_name)
                self.output.write('.')

            if node.ctx == 'store':
                self.stored_names.add(node.name)

            self.output.write(node.name)

            if use_python_bool_wrapper:
                self.output.write(')')

    def _process_getattr(self, node, **kwargs):
        """
        Processes a `GetAttr` node. e.g. {{ foo.bar }}
        """

        with self._interpolation():
            if is_loop_helper(node):
                self._process_loop_helper(node, **kwargs)
            else:
                self._process_node(node.node, **kwargs)
                self.output.write('.')
                self.output.write(node.attr)

    def _process_getitem(self, node, **kwargs):
        """
        Processes a `GetItem` node e.g. {{ foo["bar"] }}
        """

        with self._interpolation():
            if is_loop_helper(node):
                self._process_loop_helper(node, **kwargs)
            else:
                self._process_node(node.node, **kwargs)
                self.output.write('[')
                self._process_node(node.arg, **kwargs)
                self.output.write(']')

    def _process_for(self, node, **kwargs):
        """
        Processes a for loop. e.g.
            {% for number in numbers %}
                {{ number }}
            {% endfor %}
            {% for key, value in somemap.items() %}
                {{ key }} -> {{ value }}
            {% %}
        """

        # since a for loop can introduce new names into the context
        # we need to remember the ones that existed outside the loop
        previous_stored_names = self.stored_names.copy()

        with self._execution():
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

        assigns = node.target.items if isinstance(node.target, nodes.Tuple) else [node.target]

        with self._scoped_variables(assigns, **kwargs):
            for n in node.body:
                self._process_node(n, **kwargs)

        with self._execution():
            self.output.write('}')
            self.output.write(')')
            self.output.write(';')

        # restore the stored names
        self.stored_names = previous_stored_names

    def _process_if(self, node, execute_end=None, **kwargs):
        """
        Processes an if block e.g. `{% if foo %} do something {% endif %}`
        """

        with self._execution():
            self.output.write('if')
            self.output.write('(')

            with option(kwargs, use_python_bool_wrapper=True):
                self._process_node(node.test, **kwargs)

            self.output.write(')')
            self.output.write('{')

        # We accept an `execute_end` function as a keyword argument as this function is
        # recursive in the case of something like if-elif-elif-else. In these cases this
        # invocation of this function may have to close execution opened by a previous
        # invocation of this function.
        if execute_end:
            execute_end()

        # body
        for n in node.body:
            self._process_node(n, **kwargs)

        if not node.else_:
            # no else - just close the if
            with self._execution():
                self.output.write('}')

        else:
            # either an else or an elif
            with self._execution() as execute_end:
                self.output.write('}')
                self.output.write(' else ')

                # check for elif
                if isinstance(node.else_[0], nodes.If):
                    for n in node.else_:
                        self._process_node(n, execute_end=execute_end, **kwargs)
                    return

                # open up the body
                self.output.write('{')

            # process the body of the else
            for n in node.else_:
                self._process_node(n, **kwargs)

            # close the body
            with self._execution():
                self.output.write('}')

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

    def _process_call(self, node, super_block=None, **kwargs):
        if is_method_call(node, DICT_ITER_METHODS):
            self._process_node(node.node.node, **kwargs)
        elif is_method_call(node, 'super'):
            if not super_block:
                raise Exception('super() called outside of a block with a parent.')
            self._process_node(super_block, child_block=super_block, **kwargs)
        else:
            raise Exception('Usage of call with unknown method %s: %s' % (node.node.attr, node))

    def _process_filter(self, node, **kwargs):
        if node.name == 'safe':
            with self._interpolation(safe=True):
                self._process_node(node.node, **kwargs)
        else:
            raise Exception('Unsupported filter %s', node)

    def _process_assign(self, node, **kwargs):
        with self._execution():
            self.output.write('var ')
            self._process_node(node.target, **kwargs)
            self.output.write(' = ')
            self._process_node(node.node, **kwargs)
            self.output.write(';')

    def _process_scope(self, node, **kwargs):

        # keep a copy of the stored names before the scope
        previous_stored_names = self.stored_names.copy()

        assigns = [x for x in node.body if isinstance(x, nodes.Assign)]
        node.body = [x for x in node.body if not isinstance(x, nodes.Assign)]

        with self._execution():
            self.output.write('(function () {')

        with self._scoped_variables(assigns, **kwargs):
            for node in node.body:
                self._process_node(node, **kwargs)

        with self._execution():
            self.output.write('})();')

        # restore previous stored names
        self.stored_names = previous_stored_names

    def _process_compare(self, node, **kwargs):
        operand = node.ops[0].op
        use_is_equal = operand in ('eq', 'ne')

        with option(kwargs, use_python_bool_wrapper=False):

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
        with self._interpolation():
            self.output.write(json.dumps(node.value))

    def _process_list(self, node, **kwargs):
        self.output.write('[')
        for i, item in enumerate(node.items):
            self._process_node(item, **kwargs)
            if i < len(node.items) - 1:
                self.output.write(',')
        self.output.write(']')

    def _process_test(self, node, **kwargs):
        with option(kwargs, use_python_bool_wrapper=False):
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
        with self._interpolation(safe=True):
            self.output.write(self.include_fn_name)
            self.output.write('(')
            self._process_node(node.template, **kwargs)
            self.output.write(')')
            self.output.write('(')
            self.output.write(self.context_name)
            self.output.write(')')

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
        """
        Processes a math node e.g. `Div`, `Sub`, `Add`, `Mul` etc...
        If `function` is provided the expression is wrapped in a call to that function.
        """

        with self._interpolation():
            if function:
                self.output.write(function)
                self.output.write('(')

            self._process_node(node.left, **kwargs)
            self.output.write(math_operator)
            self._process_node(node.right, **kwargs)

            if function:
                self.output.write(')')

    def _process_loop_helper(self, node, **kwargs):
        """
        Processes a loop helper e.g. {{ loop.first }} or {{ loop.index }}
        """

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

    def _add_python_bool_function(self):
        """
        Adds the JS implementation of Python boolean evaluation to the top of the output.
        Although this function is very small there is no need to add it until we need it.
        It will only ever be added once.
        """

        if getattr(self, '_python_bool_function_added', False):
            return

        output = StringIO()
        output.write(PYTHON_BOOL_EVAL_FUNCTION)
        output.write(self.output.getvalue())
        self.output = output
        setattr(self, '_python_bool_function_added', True)

    @contextlib.contextmanager
    def _execution(self):
        """
        Context manager for executing some JavaScript inside a template.
        """

        def close():
            pass

        if self.state == STATE_DEFAULT:
            self.output.write('<% ')
            self.state = STATE_EXECUTING

            def close():
                if self.state == STATE_EXECUTING:
                    self.output.write(' %>')
                    self.state = STATE_DEFAULT

        yield close
        close()

    @contextlib.contextmanager
    def _interpolation(self, safe=False):

        def close():
            pass

        if self.state == STATE_DEFAULT:
            self.output.write('<%=' if safe else '<%- ')
            self.state = STATE_INTERPOLATING

            def close():
                if self.state == STATE_INTERPOLATING:
                    self.output.write(' %>')
                    self.state = STATE_DEFAULT

        yield close
        close()

    @contextlib.contextmanager
    def _scoped_variables(self, nodes_list, **kwargs):
        """
        Context manager for creating scoped variables defined by the nodes in `nodes_list`.
        These variables will be added to the context, and when the context manager exits the
        context object will be restored to it's previous state.
        """

        tmp_vars = []
        for node in nodes_list:

            is_assign_node = isinstance(node, nodes.Assign)
            name = node.target.name if is_assign_node else node.name

            # create a temp variable name
            tmp_var = self.temp_var_names.next()

            # save previous context value
            with self._execution():

                # save the current value of this name
                self.output.write('var %s = %s.%s;' % (tmp_var, self.context_name, name))

                # add new value to context
                self.output.write('%s.%s = ' % (self.context_name, name))

                if is_assign_node:
                    self._process_node(node.node, **kwargs)
                else:
                    self.output.write(node.name)

                self.output.write(';')

            tmp_vars.append((tmp_var, name))

        yield

        # restore context
        for tmp_var, name in tmp_vars:
            with self._execution():
                self.output.write('%s.%s = %s;' % (self.context_name, name, tmp_var))
