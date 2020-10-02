from datetime import datetime
import typing

from input.common import JSONObject
from lib.utils import isoparse


class NotEmptyError(Exception):
    field_list: typing.Sequence[str]

    def __init__(self, field_list: typing.Sequence[str]):
        self.field_list = field_list


def check_empty(inp: JSONObject):
    if len(inp) > 0:
        raise NotEmptyError([x for x in inp.keys()])


class TestCommonEvent(object):
    time:     datetime
    time_raw: str
    package:  str

    def __init__(self, inp: JSONObject):
        self.time_raw = inp["Time"]
        self.time = isoparse(self.time_raw)
        self.package = inp["Package"]

        del inp["Time"]
        del inp["Package"]
        del inp["Action"]


class TestRunEvent(TestCommonEvent):
    test: str

    def __init__(self, inp: JSONObject):
        super(TestRunEvent, self).__init__(inp)
        self.test = inp["Test"]

        del inp["Test"]
        check_empty(inp)


class TestPauseEvent(TestCommonEvent):
    test: str

    def __init__(self, inp: JSONObject):
        super(TestPauseEvent, self).__init__(inp)
        self.test = inp["Test"]

        del inp["Test"]
        check_empty(inp)


class TestContinueEvent(TestCommonEvent):
    test: str

    def __init__(self, inp: JSONObject):
        super(TestContinueEvent, self).__init__(inp)
        self.test = inp["Test"]

        del inp["Test"]
        check_empty(inp)


class TestPassEvent(TestCommonEvent):
    test: typing.Optional[str]
    elapsed: float

    def __init__(self, inp: JSONObject):
        super(TestPassEvent, self).__init__(inp)
        self.test = inp.pop("Test", None)
        self.elapsed = inp["Elapsed"]

        del inp["Elapsed"]
        check_empty(inp)


class TestFailEvent(TestCommonEvent):
    test: typing.Optional[str]
    elapsed: float

    def __init__(self, inp: JSONObject):
        super(TestFailEvent, self).__init__(inp)
        self.test = inp.pop("Test", None)
        self.elapsed = float(inp["Elapsed"])

        del inp["Elapsed"]
        check_empty(inp)


class TestOutputEvent(TestCommonEvent):
    test: typing.Optional[str]
    message: str

    def __init__(self, inp: JSONObject):
        super(TestOutputEvent, self).__init__(inp)
        self.test = inp.pop("Test", None)
        self.message = inp["Output"]

        del inp["Output"]
        check_empty(inp)


class TestSkipEvent(TestCommonEvent):
    test: typing.Optional[str]
    elapsed: float

    def __init__(self, inp: JSONObject):
        super(TestSkipEvent, self).__init__(inp)
        self.test = inp.pop("Test", None)
        self.elapsed = inp["Elapsed"]

        del inp["Elapsed"]
        check_empty(inp)


parse_callbacks = {
    "run": lambda x: TestRunEvent(x),
    "pause": lambda x: TestPauseEvent(x),
    "cont": lambda x: TestContinueEvent(x),
    "pass": lambda x: TestPassEvent(x),
    "fail": lambda x: TestFailEvent(x),
    "output": lambda x: TestOutputEvent(x),
    "skip": lambda x: TestSkipEvent(x),
}


TestEvent = typing.NewType("TestEvent", typing.Union[
    TestRunEvent,
    TestPauseEvent,
    TestContinueEvent,
    TestPassEvent,
    TestFailEvent,
    TestOutputEvent,
    TestSkipEvent,
])


def parse_test_line(inp: JSONObject) -> typing.Optional[TestEvent]:
    cb = parse_callbacks.get(inp["Action"], None)
    if cb is None:
        return None
    return cb(inp)
