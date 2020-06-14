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


class Printer(object):
    output: typing.TextIO

    last_node: str
    nodes: NodeList

    def __init__(self, output: typing.Optional[typing.TextIO], settings, filter_options):
        self.output = output
        if self.output is None:
            self.output = sys.stdout

        self.last_node = ""
        self.nodes = NodeList()

        self.settings = settings
        self.filter = filter_options

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

    def _print_level(self, level):
        if level == 'error':
            text = self._colored('ERR', 'red')
        elif level == 'info':
            text = self._colored('INF', 'yellow', attrs=['bold'])
        elif level == 'debug':
            text = self._colored('DBG', 'yellow')
        elif level == 'warn':
            text = self._colored('WRN', 'magenta')
        elif level == 'panic':
            text = self._colored('FTL', 'black', 'on_red')
        else:
            text = self._colored(level, 'yellow')

        self.output.write(text)

    def _print_fields(self, fields):
        field_keys = []
        for field in sorted(fields.keys()):
            if not self.filter.skip_field(field, fields[field]):
                field_keys.append(field)

        if len(field_keys) == 0:
            return

        self.output.write(self._colored('[', 'green'))
        first = True
        for key in field_keys:
            if not first:
                self.output.write(', ')
            else:
                first = False

            self.output.write(self._colored(str(key), 'green'))
            self.output.write('=')
            if isinstance(fields[key], str) and fields[key].startswith('insolar:'):
                self.output.write(self.nodes.emoji_get(fields[key]))
            else:
                self.output.write(repr(fields[key]))
        self.output.write(self._colored(']', 'green'))

    def _print_header(self, line: LogLine):
        node_id = line.node
        role = line.role
        pulse = line.pulse

        new_node = False
        if self.last_node != node_id:
            new_node = True
            self.last_node = node_id

        new_pulse = False
        node = self.nodes.node_get(line)
        if node is None:
            new_pulse = True
            node = self.nodes.node_replace(line)
        elif pulse is None or node.pulse is None:
            pass
        elif node.pulse == pulse:
            pass

        else:
            new_pulse = True
            node.pulse = pulse

        if new_node or new_pulse:
            self.output.write('\nNode %s - %s - %s ===\n' % (node.emoji, role, pulse))

    def print_line(self, line: typing.Union[LogLine, RawLine]):
        # format is like <path>/<instance>/output.log:<line>:<datetime> <LVL> <message>
        if isinstance(line, RawLine):
            self.output.write(self._colored(line.message, 'cyan'))
            self.output.write('\n')
        else:
            self._print_header(line)
            self.output.write('[')
            self.output.write(line.timestamp.strftime('%H:%M:%S.%f'))
            self.output.write(', ')
            self._print_level(line.level)
            self.output.write('] - ')
            self.output.write(self._colored(line.message, 'cyan'))
            self.output.write(' ')
            self._print_fields(line.fields)
            self.output.write('\n')
            if line.backtrace is not None:
                self.output.write(line.backtrace)

    def print_lines(self, lines):
        for line in lines:
            self.print_line(line)
