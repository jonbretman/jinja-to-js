# Jinja to JS
Converts Jinja2 templates into Underscore/Lo-Dash templates for use in the browser. Not all Jinja2 features are supported, this readme explains the ones that are.

#### Why Underscore/Lo-Dash
The Underscore/Lo-Dash library provides a lot of functional utilities that make implementing the features of Jinja much easier than it would be in other popular JavaScript templating languages like Mustache.

#### API
```python
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja_to_js import JinjaToJS

loader = FileSystemLoader('/path/to/templates/')
environment = Environment(loader=loader, extensions=['jinja2.ext.with_'])
compiler = JinjaToJS(environment, template_name='my_template.jinja')
underscore_template = compiler.get_output()
```

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

##### Comments
[Jinja Docs](http://jinja.pocoo.org/docs/dev/templates/#comments)

Jinja comments are ignored by parser API so do not show up in the resulting Underscore template. HTML comments are preserved though.

```
{# This comment will not appear in the Underscore template #}
<!-- This comment will appear in the Underscore template -->
```
