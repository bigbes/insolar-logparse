import sys
import typing

from line.log import LogLine, NodeList, RawLine

try:
    from termcolor import colored
except ImportError:
    sys.stderr.write('WARN: termcolor library not found, colors aren\'t available\n')
    sys.stderr.write('WARN: install termcolor using: `pip3 install termcolor` \n')

    def colored(string, *args, **kwargs) -> str:
        return string


class Aggregator(object):
    def __input__(self):


class Printer(object):
    output: typing.TextIO

    def __init__(self, output: typing.Optional[typing.TextIO], settings):
        self.output = output
        if self.output is None:
            self.output = sys.stdout

        if settings.force_color:
            self.colored = True
        elif not self.output.isatty():
            self.colored = False
        else:
            self.colored = True

    def _colored(self, string: str, *args, **kwargs) -> str:
        if not self.colored:
            return string
        return colored(string, *args, **kwargs)
