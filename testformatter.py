#!/usr/bin/env python3

import argparse
import sys

from aggregator.run import OverallInformation
from input.test import TestReader


def prepare_parser():
    parser = argparse.ArgumentParser(description='Parse JSON test output of insolar')
    return parser


def main() -> int:
    parser = prepare_parser()
    args = parser.parse_args()

    reader = TestReader(None, debug=True)
    info = OverallInformation()

    for line in reader.read_generator():
        info.add_event(line)
    brief = info.brief_failed()
    for run in brief:
        print("FAIL: %s" % run.name)
        print("=" * 80)
        for out in run.output:
            print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
