[![Build Status](https://travis-ci.org/jonbretman/jinja-to-js.svg?branch=master)](https://travis-ci.org/jonbretman/jinja-to-js)

# Jinja to JS
Converts [Jinja2](http://jinja.pocoo.org/docs/dev/) templates into JavaScript functions so that they can be used in JavaScript environments.

## What is it?
Jinja2 is a very fast templating language and therefore is ideal for use with Python web frameworks like Django, however there are many use cases for wanting to share the same template between the server and the browser. Instead of writing a Jinja implementation in JavaScript (there are already a few of those) jinja-to-js uses the Python Jinja2 library to parse a template into an AST (http://jinja.pocoo.org/docs/dev/api/#jinja2.Environment.parse) and uses that AST to output a JavasScript function/module. By only relying on one parsing implementation you can be sure that your templates will produce the same result whether used from Python or JavaScript.

## Example

First install jinja-to-js using `pip`:
```sh
$ pip install jinja-to-js
```

Lets assume we have a Jinja template called **names.jinja** in a templates directory located at **./src/templates**.
```jinja
{% for name in names %}
    {{ name }}
{% endfor %}
```

We can turn this into an ES6 JavaScript module like so:
```sh
$ jinja_to_js ./src/templates names.jinja -o names.js -m es6
```

**names.js** will now contain:
```js
import jinjaToJS from 'jinja-to-js';

export default function templateNames(context) {
    /* JS code here */
};
```

#### JavaScript Runtime
Not the first line where the output module imports the [jinja-to-js](https://www.npmjs.com/package/jinja-to-js) package. This can be installed from npm like shown below and is required. It is very small though and means that common code like HTML escaping doesn't need to be duplicated in each template.

```sh
$ npm install jinja-to-js
```

#### JavaScript Module Formats
The `-m` option (long version `--js-module-format`) specifies the module type, which can be `amd`, `commonjs`, `es6` or not provided at all which will result in jinja-to-js just outputting a named JS function. 

See `jinja_to_js --help` for all available options.

```
$ jinja_to_js --help
usage: jinja_to_js [-h] [-o [OUTFILE]] [-m [JS_MODULE_FORMAT]]
                   [-r [RUNTIME_PATH]] [-p [INCLUDE_PREFIX]]
                   [-i [INCLUDE_EXT]]
                   template_root template_name

Convert Jinja templates into JavaScript functions.
--------------------------------------------------

Three different JavaScript modules formats are supported:

  Global: the output will be a named function.
  AMD: the output will be an AMD module
  ES6: the output will be an ES6 module with a default export.

positional arguments:
  template_root         Specifies the root directory where all templates
                        should be loaded from.
  template_name         Specifies the input file (relative to the template
                        root).

optional arguments:
  -h, --help            show this help message and exit
  -o [OUTFILE], --output [OUTFILE]
                        Specifies the output file. The default is stdout.
  -m [JS_MODULE_FORMAT], --js-module-format [JS_MODULE_FORMAT]
                        Specifies the JS module format.
  -r [RUNTIME_PATH], --runtime-path [RUNTIME_PATH]
                        Specifies the import path for the jinja-to-js JS
                        runtime.
  -p [INCLUDE_PREFIX], --include-prefix [INCLUDE_PREFIX]
                        Specifies the prefix to use for included templates.
  -i [INCLUDE_EXT], --include-ext [INCLUDE_EXT]
                        Specifies the extension to use for included templates.
```

## Supported Features
* `if` statements [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#if)
* `if` expressions [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#if-expression)
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

Includes are handled differently depending on what `--js-module-format` is set to. 

**No module format**: If it is not set then jinja-to-js will just output a named JavaScript function that will expect the jinja-to-js JavaScript runtime to be available in scope as `jinjaToJS` and to have a method called `include` available on it (you have to implement this method yourself). This option may be useful if you want to implement your own custom wrapper.

**AMD, CommonJS, and ES6**: For these module types the respective import mechanism will be used. For `commonjs` and `es6` module formats imports will be relative in respect to the current template, and for `amd` they will be left "as is" with `--include-prefix` added to the beginning. For all module formats there will be no extension unless you specify one using `--include-ext`.

#### Template Inheritance [(Jinja Docs)](http://jinja.pocoo.org/docs/dev/templates/#template-inheritance)

Template inheritance is supported, including the `{{ super() }}` function. The name of the template to be extended from must be a string literal as it needs to be loaded at compile time.

**parent.jinja**
```jinja
{% block content %}
    The default content.
{% endblock
```

**child.jinja**
```jinja
{% extends 'parent.jinja' %}
{% block content %}
    {{ super() }}
    Additional content.
{% endblock %}
```
