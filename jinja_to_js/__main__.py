from __future__ import absolute_import, unicode_literals
import sys
import argparse

from . import JinjaToJS


def main():

    args = sys.argv[1:]

    parser = argparse.ArgumentParser(usage='python -m jinja_to_js [options]')

    parser.add_argument(
        "-f", "--file", nargs='?', type=argparse.FileType('r'),
        help="Specifies the input file.  The default is stdin.",
        default=sys.stdin, dest="infile"
    )

    parser.add_argument(
        "-o", "--output", nargs='?', type=argparse.FileType('w'),
        help="Specifies the output file.  The default is stdout.",
        default=sys.stdout, dest="outfile"
    )

    parser.add_argument(
        "-m", "--js-module-format", nargs='?',
        help="Specifies the JS module format.",
        dest="js_module_format"
    )

    parser.add_argument(
        "-r", "--runtime-path", nargs='?',
        help="Specifies the import path for the jinja-to-js JS runtime.",
        default='jinja-to-js',
        dest="runtime_path"
    )

    parser.add_argument(
        "-i", "--include-ext", nargs='?',
        help="Specifies the extension to use for included templates.",
        default='',
        dest="include_ext"
    )

    parser.add_argument(
        "-p", "--include-prefix", nargs='?',
        help="Specifies the prefix to use for included templates.",
        default='',
        dest="include_prefix"
    )

    options = parser.parse_args(args)

    jinja_template = options.infile.read()
    if hasattr(jinja_template, 'decode'):
        jinja_template = jinja_template.decode('utf-8')

    compiler = JinjaToJS(template_string=jinja_template,
                         js_module_format=options.js_module_format,
                         runtime_path=options.runtime_path,
                         include_ext=options.include_ext,
                         include_prefix=options.include_prefix)

    options.outfile.write(compiler.get_output())
    return 0
