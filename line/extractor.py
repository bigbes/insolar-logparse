import re

import typing

fatal_prefix = 'FATAL: '

force_color: bool = None


class Line(object):
    def __init__(self, instance, json_line):
        self.instance = instance
        self.json_line = json_line


class LineExtractor(object):
    re: typing.Collection[typing.Pattern] = [
        re.compile('[0-9\-TZ]+ .+-(\d+) [^ ]+: ({.*})'),  # time host-%d ???: <log>
        re.compile('[0-9\-TZ]+ (\d+)/insolard_.*.log ({.*})'),  # time host-%d ???: <log>
        re.compile('(\d+)/\w+.log:\d+:({.*})'),  # dir-%d/output.log:line:<log>
        re.compile('(\d+)/\w+.log:({.*})'),  # dir-%d/output.log:<log>
        re.compile('()({.*})')
    ]
    extractor: typing.Optional[typing.Pattern]

    def __init__(self):
        self.extractor = None

    @staticmethod
    def _deduce_extractor(line: str) -> typing.Optional[typing.Pattern]:
        for line_regexp in LineExtractor.re:
            match = line_regexp.search(line)
            if match is not None:
                return line_regexp
        return None

    def __call__(self, raw_line: str) -> typing.Optional[Line]:
        if self.extractor is None:
            self.extractor = self._deduce_extractor(raw_line)
        if self.extractor is None:
            return None
        match = self.extractor.search(raw_line)
        if match is None:
            self.extractor = self._deduce_extractor(raw_line)
            if self.extractor is None:
                return None
            match = self.extractor.search(raw_line)
            if match is None:
                return None
        return Line(match.group(1), match.group(2))
