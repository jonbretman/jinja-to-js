from __future__ import absolute_import, unicode_literals

import sys

import argparse

from . import JinjaToJS


DESCRIPTION = """
Convert Jinja templates into JavaScript functions.
--------------------------------------------------

Three different JavaScript modules formats are supported:

  Global: the output will be a named function.
  AMD: the output will be an AMD module
  ES6: the output will be an ES6 module with a default export.
"""


def get_arg_parser():

    parser = argparse.ArgumentParser(description=DESCRIPTION,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        "template_root",
        help="Specifies the root directory where all templates should be loaded from."
    )

    parser.add_argument(
        "template_name",
        help="Specifies the input file (relative to the template root)."
    )

    parser.add_argument(
        "-o", "--output", nargs='?', type=argparse.FileType('w'),
        help="Specifies the output file.  The default is stdout.",
        default=sys.stdout,
        dest="outfile"
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
        "-p", "--include-prefix", nargs='?',
        help="Specifies the prefix to use for included templates.",
        default='',
        dest="include_prefix"
    )

    parser.add_argument(
        "-i", "--include-ext", nargs='?',
        help="Specifies the extension to use for included templates.",
        default='',
        dest="include_ext"
    )

    parser.add_argument(
        "-f", "--filters", nargs='*',
        help="Specifies custom filters to be allowed.",
        default='',
        dest="custom_filters"
    )

    return parser


def get_init_kwargs(options):
    kwargs = {}
    for key, value in vars(options).items():
        if key != 'outfile':
            kwargs[key] = value
    return kwargs


def main():
    parser = get_arg_parser()
    options = parser.parse_args()
    compiler = JinjaToJS(**get_init_kwargs(options))
    options.outfile.write(compiler.get_output())
    return 0
