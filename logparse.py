#!/usr/bin/env python3

import argparse
import sys

from lib.filter import FilterOptions
from printer.log import Printer
from input.log import SingleReader


def prepare_parser():
    parser = argparse.ArgumentParser(description='Parse JSON logs of insolar')
    parser.add_argument(
        '--skip-field',
        dest='skip_field',
        action='append',
        default=[],
        help='fields to skip'
    )
    parser.add_argument(
        '--skip-caller',
        dest='skip_caller',
        action='append',
        default=[],
        help='caller to skip'
    )
    parser.add_argument(
        '--force-color',
        action='store_true',
        default=False,
        help='force colored output'
    )
    parser.add_argument(
        '--filter-message',
        action='append',
        default=[],
        help='show only messages that contains string'
    )
    parser.add_argument(
        '--assume-sorted',
        action='store_false',
        default=True,
        help='disable sorting of input'
    )
    parser.add_argument(
        '--use-nodeid',
        action='store_true',
        default=False,
        help='enable using of nodeid instead of input'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='verbose'
    )
    return parser


def main() -> int:
    parser = prepare_parser()
    args = parser.parse_args()

    filter_options = FilterOptions(args)
    reader = SingleReader(sys.stdin, filter_options, debug=args.verbose)
    printer = Printer(sys.stdout, args, filter_options)

    if args.assume_sorted:
        for line in reader.read_generator():
            printer.print_line(line)
    else:
        printer.print_lines(reader.read_sorted())

    return 0


if __name__ == "__main__":
    sys.exit(main())
