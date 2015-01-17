import contextlib

from cStringIO import StringIO
from jinja2 import nodes
from jinja2.nodes import Call, Getattr


def compile_template(env, loader, template_name):
    """
    Compiles the template with the given name into an
    Underscore template for use in the browser.
    """

    template_string, _, _ = loader.get_source(env, template_name)
    parsed = env.parse(template_string)
    return Compiler(parsed).get_output()


OPTION_INSIDE_IF = 'inside_if'
OPTION_INSIDE_BLOCK = 'inside_block'

INTERPOLATION_START = '<%- '
INTERPOLATION_END = ' %>'
PROPERTY_ACCESSOR = '.'
EXECUTE_START = '<% '
EXECUTE_END = ' %>'
BLOCK_OPEN = '{'
BLOCK_CLOSE = '}'
COMMA = ', '
FUNCTION = 'function'
PAREN_START = ' ('
PAREN_END = ') '
EACH_START = '_.each('
VALUES_START = '_.values('
KEYS_START = '_.keys('
EACH_END = '});'
IF = 'if'
ELSE = ' else '
NOT = '!'
OR = ' || '
AND = ' && '
OPERANDS = {
    'eq': ' === ',
    'ne': ' !== ',
    'lt': ' < ',
    'gt': ' > '
}


@contextlib.contextmanager
def option(kwargs, key, value):
    old_value = kwargs.get(key)
    kwargs[key] = value
    try:
        yield
    finally:
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


class Compiler(object):

    def __init__(self, ast):
        self.output = StringIO()
        self.stored_names = set()
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
            print 'Unknown node %s' % node

    def _process_output(self, node, **kwargs):
        for n in node.nodes:
            self._process_node(n, **kwargs)

    def _process_templatedata(self, node, **_):
        self.output.write(node.data)

    def _process_name(self, node, **kwargs):
        if not kwargs.get(OPTION_INSIDE_BLOCK):
            self.output.write(INTERPOLATION_START)

        if node.name not in self.stored_names and node.ctx != 'store':
            self.output.write('context.')

        if node.ctx == 'store':
            self.stored_names.add(node.name)

        self.output.write(node.name)

        if not kwargs.get(OPTION_INSIDE_BLOCK):
            self.output.write(INTERPOLATION_END)

    def _process_getattr(self, node, **kwargs):
        if not kwargs.get(OPTION_INSIDE_BLOCK):
            self.output.write(INTERPOLATION_START)

        with option(kwargs, OPTION_INSIDE_BLOCK, True):
            self._process_node(node.node, **kwargs)
            self.output.write(PROPERTY_ACCESSOR)
            self.output.write(node.attr)

        if not kwargs.get(OPTION_INSIDE_BLOCK):
            self.output.write(INTERPOLATION_END)

    def _process_for(self, node, **kwargs):
        # since a for loop can introduce new names into the context
        # we need to remember the ones that existed outside the loop
        previous_stored_names = self.stored_names.copy()

        self.output.write(EXECUTE_START)
        if is_method_call(node.iter, 'values'):
            self.output.write(VALUES_START)
        elif is_method_call(node.iter, 'keys'):
            self.output.write(KEYS_START)
        else:
            self.output.write(EACH_START)

        with option(kwargs, OPTION_INSIDE_BLOCK, True):
            self._process_node(node.iter, **kwargs)

        self.output.write(COMMA)
        self.output.write(FUNCTION)
        self.output.write(PAREN_START)

        with option(kwargs, OPTION_INSIDE_BLOCK, True):
            self._process_node(node.target, **kwargs)

        self.output.write(PAREN_END)
        self.output.write(BLOCK_OPEN)
        self.output.write(EXECUTE_END)

        # body
        for n in node.body:
            self._process_node(n, **kwargs)

        self.output.write(EXECUTE_START)
        self.output.write(EACH_END)
        self.output.write(EXECUTE_END)

        # restore the stored names
        self.stored_names = previous_stored_names

    def _process_if(self, node, **kwargs):
        # condition
        with option(kwargs, OPTION_INSIDE_BLOCK, True):
            if not kwargs.get(OPTION_INSIDE_IF):
                self.output.write(EXECUTE_START)
            self.output.write(IF)
            self.output.write(PAREN_START)
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
                with option(kwargs, OPTION_INSIDE_IF, True):
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
        if len(node.items) != 2:
            print node
            raise Exception('Only tuples with 2 items are supported')

        self._process_node(node.items[1], **kwargs)
        self.output.write(COMMA)
        self._process_node(node.items[0], **kwargs)

    def _process_call(self, node, **kwargs):
        if is_method_call(node, ('iteritems', 'items', 'values', 'keys')):
            self._process_node(node.node.node, **kwargs)

        print 'Usage of call %s' % node

    def _process_filter(self, node, **kwargs):
        self._process_node(node.node, **kwargs)
        print 'Usage of filter: %s' % node.name

    def _process_ccope(self, node, **kwargs):
        for n in node.body:
            self._process_node(n, **kwargs)

    def _process_compare(self, node, **kwargs):
        self._process_node(node.expr, **kwargs)
        for n in node.ops:
            self._process_node(n, **kwargs)

    def _process_operand(self, node, **kwargs):
        operand = OPERANDS.get(node.op)
        if not operand:
            raise Exception('Unknown operand %s' % node.op)
        self.output.write(operand)
        self._process_node(node.expr, **kwargs)

    def _process_const(self, node, **_):
        if isinstance(node.value, basestring):
            self.output.write("'")
            self.output.write(str(node.value))
            self.output.write("'")

        elif isinstance(node.value, int):
            self.output.write(str(node.value))

        else:
            raise Exception('Unknown Const type %s' % type(node.value))

    def _process_include(self, node, **kwargs):
        raise NotImplemented()

    def _process_block(self, node, **_):
        pass
