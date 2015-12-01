from __future__ import absolute_import, unicode_literals
import os
import sys
import argparse

from . import JinjaToJS


def main():

    args = sys.argv[1:]

    parser = argparse.ArgumentParser(usage='python -m jinja_to_js [options]')

    parser.add_argument(
        "-f", "--file", nargs='?',
        help="Specifies the input file relative to --template-root. "
             "If not specific will default to stdin.",
        default=None, dest="template_name"
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

    parser.add_argument(
        "-t", "--template-root", nargs='?',
        help="Specifies the root directory where all templates should be loaded from.",
        default=os.getcwd(),
        dest="template_root"
    )

    options = parser.parse_args(args)

    template_string = None
    if options.template_name is None:
        template_string = sys.stdin.read()

    compiler = JinjaToJS(template_name=options.template_name,
                         template_string=template_string,
                         template_root=options.template_root,
                         js_module_format=options.js_module_format,
                         runtime_path=options.runtime_path,
                         include_ext=options.include_ext,
                         include_prefix=options.include_prefix)

    options.outfile.write(compiler.get_output())
    return 0
