import copy
import datetime
import typing

from lib.emoji import random_emoji
from lib.utils import isoparse


class RawLine(object):
    message: str

    def __init__(self, message: str):
        self.message = message.rstrip()


class LogLine(object):
    node: str
    role: str
    level: str
    caller: typing.Optional[str]
    message: str
    traceid: str
    timestamp_raw: str
    timestamp: datetime.datetime
    fields: typing.Mapping[str, typing.Any]

    backtrace: typing.Optional[str]
    pulse: typing.Optional[str]

    def __init__(self, line: typing.Dict[str, typing.Any]):
        old_line = line
        line = copy.copy(line)

        self.node = line.pop('nodeid', "<empty>")
        self.role = line.pop('role')
        self.message = line.pop('message').strip()
        self.timestamp_raw = line.pop('time')
        self.timestamp = isoparse(self.timestamp_raw)
        if 'caller' not in line:
            self.caller = None
        else:
            self.caller = line.pop('caller')

        self.backtrace = line.pop('Backtrace', None)
        if self.backtrace is None:
            self.backtrace = line.pop('backtrace', None)

        self.level = line.pop('level')
        if self.message.startswith('FATAL: '):
            self.level = 'fatal'

        self.traceid = line.get('traceid', None)

        pulse = line.pop('pulse', None)
        if pulse is None:
            pulse = line.pop('new_pulse', None)
        if isinstance(pulse, (list, tuple)):
            pulse = pulse[0]
        self.pulse = pulse

        self.fields = line
        del self.fields['writeDuration']
        del self.fields['loginstance']


class NodeDefinition(object):
    def __init__(self, node_id: str, role: str, pulse: typing.Optional[str], emoji: str):
        self.role = role
        self.node_id = node_id
        self.pulse = pulse
        self.emoji = emoji


class NodeList(object):
    node_list: typing.Dict[str, NodeDefinition]
    node_emojis: typing.Dict[str, str]

    def __init__(self):
        self.node_list = {}
        self.node_emojis = {}

    def emoji_generate(self):
        while True:
            emoji = random_emoji()[0]
            if emoji not in self.node_emojis.values():
                break

        return emoji

    def emoji_create_or_get(self, id: str):
        if id not in self.node_emojis:
            emoji = self.emoji_generate()
            self.node_emojis[id] = emoji
        else:
            emoji = self.node_emojis[id]

        return emoji

    def emoji_get(self, id: str) -> str:
        if id not in self.node_emojis:
            return id
        return self.node_emojis[id]

    def node_replace(self, line: LogLine) -> NodeDefinition:
        emoji = self.emoji_create_or_get(line.node)
        self.node_list[line.node] = NodeDefinition(line.node, line.role, line.pulse, emoji)
        return self.node_list[line.node]

    def node_get(self, line: LogLine) -> typing.Optional[NodeDefinition]:
        return self.node_list.get(line.node, None)
