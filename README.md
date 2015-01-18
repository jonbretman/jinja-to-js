# Jinja to JS
Converts Jinja2 templates into Underscore/Lo-Dash templates so that they can be used in the browser.

#### How it works
First the Jinja template is [parsed into an AST](http://jinja.pocoo.org/docs/dev/api/#jinja2.Environment.parse), and then from that an Underscore style template string is created. This string can then be compiled into a JavaScript function using the `_.template` function. Docs for the `_.template` function can be found [here](http://underscorejs.org/#template) for Underscore and [here](https://lodash.com/docs#template) for Lo-Dash. It is important that when the template is compiled the `variable` option is set to `"context"`.

The Underscore/Lo-Dash libraries provides a lot of functional utilities that make implementing the features of Jinja quite easy. As such the compiled template functions require that Underscore/Lo-Dash are available.

#### Example
```python
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja_to_js import JinjaToJS

loader = FileSystemLoader('/path/to/templates/')
environment = Environment(loader=loader, extensions=['jinja2.ext.with_'])
compiler = JinjaToJS(environment, template_name='my_template.jinja')
underscore_template = compiler.get_output()
```

#### Options
* `environment` (**required**) A Jinja environment with a `loader`.
* `template_name` The name of the template to convert.
* `template_string` A Jinja template string.
* `include_fn_name` The function to call when a template needs to be included.

#### Supported Features

##### If statements
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#if)

Truthy / falsey tests behave as expected so empty lists (JS arrays) or empty dicts (JS objects) are evaluated to be false. This is achieved by using the `_.isEmpty` function.
```jinja
{% if foo %}
    {{ foo }}
{% endif %}
```

##### Comparisons
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#comparisons)

The comparitors `==`, `!=`, `<`, `>`, `<=`, and `>=` are all supported. Equality checking behaves as expected so for example `[1, 2, 3] == [1, 2, 3]` is true. This achieved by using the `_.isEqual` function.
```jinja
{% if foo == 5 %}
    foo is 5
{% endif %}
```

##### Logic
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#logic)

Logic operators `and`, `or`, `not` are all supported.
```jinja
{% if not foo and bar or baz %}

{% endif %}
```

##### Iteration
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#for)

Iteration is supported by using the `_.each` function. The `dict` methods `items`, `iteritems`, `values`, and `keys` all work as expected, which is achieved using the `_.keys` and `_.values` methods. 
```jinja
{% for thing in things %}
    {{ thing }}
{% endfor %}

{% for key, value in my_object.items() %}
    {{ key }} -> {{ value }}
{% endfor %}
```

##### Loop Helpers
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#for)

Loop helpers are only supported for lists (JS arrays). The following helpers are supported:
* `loop.index`
* `loop.index0`
* `loop.first`
* `loop.last`
* `loop.length`


##### Tests
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#tests)

The only test that is currently supported is `defined` and `undefined`.
```jinja
{% if foo is defined %}
    {{ foo }}
{% endif %}

{% if foo is undefined %}
    foo is not defined
{% endif %}
```

##### With
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#with-statement)

The `{% with %}` tag is supported for creating a new scope.
```jinja
{% with %}
    {% set foo = True %}
{% endwith %}
```

##### Assignment
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#assignments)

Assignment is supported via `{% set %}` although currently only for strings, numbers, booleans, and context variables.
```jinja
{% set foo = True %}
{% set bar = 'some string' %}
{% set baz = some_context_variable %}
```

##### Includes
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#include)

Includes are supported by taking the following steps:

* A function dictated by `include_fn_name` is called with the name of the template to be included as the only argument. The default value of `include_fn_name` is `context.include`. This function **MUST** return a compiled template function
* The returned function is called with the current context as it's only argument.
* The return value of this function is output into the current template.

The following shows a simple example of this in practice.
```js
var templates = {
    template_1: theCompiledFnForTemplate1,
    template_2: theCompiledFnForTemplate2
};

function getTemplate(name) {
    return templates[name];
}

function render(name, context) {
    context.include = getTemplate;
    return getTemplate(name)(context);
}
```

##### Comments
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#comments)

Jinja comments are ignored by parser API so do not show up in the resulting Underscore template. HTML comments are preserved though.

```
{# This comment will not appear in the Underscore template #}
<!-- This comment will appear in the Underscore template -->
```
