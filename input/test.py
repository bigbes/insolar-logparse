import json
import sys
import typing

from input.common import json_object_multiple_unique
from line.test import TestCommonEvent, parse_test_line


class TestReader(object):
    input: typing.TextIO

    def __init__(self, inp: typing.Optional[typing.TextIO], **kwargs):
        self.input = inp
        if self.input is None:
            self.input = sys.stdin

        self.debug = kwargs.get("debug", False)

    def read_line(self) -> typing.Union[TestCommonEvent, None]:
        while True:
            raw_line = self.input.readline()
            if raw_line is None or raw_line == "":
                return None

            try:
                parsed_line = json.loads(raw_line, object_pairs_hook=json_object_multiple_unique)
            except Exception as e:
                if self.debug:
                    print("failed to parse json [%s]: '%s'" % (str(e), raw_line), file=sys.stderr)
                continue

            try:
                test_line = parse_test_line(parsed_line)
            except Exception as e:
                if self.debug:
                    print("failed to disassemble log line [%s]: '%s'" % (str(e), raw_line), file=sys.stderr)
                continue

            return test_line

    def read_generator(self) -> typing.Generator[TestCommonEvent, None, None]:
        while True:
            line = self.read_line()
            if line is None:
                return None
            yield line

