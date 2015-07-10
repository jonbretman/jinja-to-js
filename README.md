[![Build Status](https://travis-ci.org/jonbretman/jinja-to-js.svg?branch=master)](https://travis-ci.org/jonbretman/jinja-to-js)

# Jinja to JS
Converts [Jinja2](http://jinja.pocoo.org/docs/dev/) templates into JavaScript functions so that they can be used in the browser.

## What is it?
Jinja2 is a very fast templating language and therefore is ideal for use with Python web framework like Django, however there are many use cases for wanting to share the same template between the server and the browser. Instead of writing a Jinja implementation in JavaScript (there are already a few of those) jinja-to-js uses the Python Jinja2 library to parse a template into an AST (http://jinja.pocoo.org/docs/dev/api/#jinja2.Environment.parse) and uses that AST to output a JavasScript function/module.

## Example

First install jinja-to-js using `pip`:
```sh
$ pip install jinja-to-js
```

Lets assume we have a Jinja template called **names.jinja**.
```jinja
{% for name in names %}
    {{ name }}
{% endfor %}
```

We can turn this into a JavaScript module like so:
```sh
$ jinja_to_js -f ./names.jinja -o ./names.js -m es6
```

**names.js** will now contain:
```js
export default function template(context) {
    /* JS code here */
};
```

The `-m` option specified the module type, which can be `amd`, `commonjs`, `es6` or not provided at all which will result in jinja-to-js just outputting a named JS function.

## Supported Features
* `if` statements [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#if)
* `for` [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#for) - see below for supported loop helpers
* `with` [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#with-statement)
* `include` [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#include) - see below for example
* comparisons [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#comparisons)
* logic [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#logic)
* tests [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#tests) - see below for supported tests
* filters [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#builtin-filters) - see below for supported filters
* assignment [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#assignments)
* comments [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#comments)

### Supported tests
* `defined` - [docs](http://jinja.pocoo.org/docs/dev/templates/#defined)
* `undefined` - [docs](http://jinja.pocoo.org/docs/dev/templates/#undefined)
* `callable` - [docs](http://jinja.pocoo.org/docs/dev/templates/#callable)
* `divisibleby` - [docs](http://jinja.pocoo.org/docs/dev/templates/#divisibleby)
* `even` - [docs](http://jinja.pocoo.org/docs/dev/templates/#even)
* `odd` - [docs](http://jinja.pocoo.org/docs/dev/templates/#odd)
* `none` - [docs](http://jinja.pocoo.org/docs/dev/templates/#none)
* `number` - [docs](http://jinja.pocoo.org/docs/dev/templates/#number)
* `upper`
* `lower`
* `string`
* `mapping`

### Supported filters
* `safe` - [docs](http://jinja.pocoo.org/docs/dev/templates/#safe)
* `capitalize` - [docs](http://jinja.pocoo.org/docs/dev/templates/#capitalize)
* `abs` - [docs](http://jinja.pocoo.org/docs/dev/templates/#abs)
* `attr` - [docs](http://jinja.pocoo.org/docs/dev/templates/#attr)
* `batch` - [docs](http://jinja.pocoo.org/docs/dev/templates/#batch)
* `default` - [docs](http://jinja.pocoo.org/docs/dev/templates/#default)
* `first` - [docs](http://jinja.pocoo.org/docs/dev/templates/#first)
* `int` - [docs](http://jinja.pocoo.org/docs/dev/templates/#int)
* `last` - [docs](http://jinja.pocoo.org/docs/dev/templates/#last)
* `length` - [docs](http://jinja.pocoo.org/docs/dev/templates/#length)
* `lower` - [docs](http://jinja.pocoo.org/docs/dev/templates/#lower)
* `slice` - [docs](http://jinja.pocoo.org/docs/dev/templates/#slice)
* `title` - [docs](http://jinja.pocoo.org/docs/dev/templates/#title)
* `trim` - [docs](http://jinja.pocoo.org/docs/dev/templates/#trim)
* `upper` - [docs](http://jinja.pocoo.org/docs/dev/templates/#upper)
* `truncate` - [docs](http://jinja.pocoo.org/docs/dev/templates/#truncate)

#### Loop Helpers
[(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#for)

Loop helpers will only work for lists (JS arrays). The following helpers are supported:
* `loop.index`
* `loop.index0`
* `loop.first`
* `loop.last`
* `loop.length`

#### Includes [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#include)

Includes are supported by taking the following steps:

* If a template contain an include, for example `{% include 'bar.jinja' %}`, then you must provide a function called `include` on the context object passed to the template. This function will be called with the name of the template to be included and should return the compiled version of this template.
* The returned template function is called with the current context as it's only argument.
* The return value of this function is output into the current template.

The following shows a simple example of this in practice.
```js
var templates = {
    'bar': theCompiledFnForBar,
    'foo': theCompiledFnForFoo
};

function getTemplate(name) {
    return templates[name.replace(/\.jinja$/, '')];
}

function render(name, context) {
    context.include = getTemplate;
    return getTemplate(name)(context);
}

render('foo');
```

#### Template Inheritance [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#template-inheritance)

Template inheritance is supported, including the `{{ super() }}` function. The name of the template to be extended from must be a string literal as it needs to be loaded at compile time.

**Parent**
```jinja
{% block content %}
    The default content.
{% endblock
```

**Child**
```jinja
{% block content %}
    {{ super() }}
    Additional content.
{% endblock %}
```
