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

    options = parser.parse_args(args)

    jinja_template = options.infile.read()
    if hasattr(jinja_template, 'decode'):
        jinja_template = jinja_template.decode('utf-8')

    compiler = JinjaToJS(template_string=jinja_template)

    options.outfile.write(compiler.get_output())
    return 0
