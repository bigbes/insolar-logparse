import json
import sys
import typing

from input.common import json_object_multiple_unique
from lib.filter import FilterOptions
from line.log import LogLine, RawLine
from line.extractor import LineExtractor


class SingleReader(object):
    def __init__(self, inp: typing.Optional[typing.TextIO], filter_options: FilterOptions, **kwargs):
        self.input = inp
        if self.input is None:
            self.input = sys.stdin
        self.filter = filter_options

        self.extractor = LineExtractor()

        self.debug = kwargs.get("debug", False)

    def read_line(self) -> typing.Union[LogLine, RawLine, None]:
        while True:
            raw_line = self.input.readline()
            if raw_line is None or raw_line == "":
                return None

            line = self.extractor(raw_line)
            if line is None:
                return RawLine(raw_line)

            try:
                raw_parsed_line = json.loads(line.json_line, object_pairs_hook=json_object_multiple_unique)
            except Exception as e:
                if self.debug:
                    print("failed to parse json [%s]: '%s'" % (str(e), line.json_line), file=sys.stderr)
                return RawLine(raw_line)

            log_line: LogLine
            try:
                log_line = LogLine(raw_parsed_line)
            except Exception as e:
                if self.debug:
                    print("failed to disassemble log line [%s]: '%s'" % (str(e), line.json_line), file=sys.stderr)
                return RawLine(raw_line)

            if not self.filter.filter_log_line(log_line):
                return log_line

    def read_generator(self) -> typing.Generator[LogLine, None, None]:
        while True:
            line = self.read_line()
            if line is None:
                return None
            yield line

    def read_all(self) -> typing.Collection[LogLine]:
        return [line for line in self.read_generator()]

    def read_sorted(self) -> typing.Collection[LogLine]:
        lines = self.read_all()
        return sorted(lines, key=lambda x: x.timestamp)
