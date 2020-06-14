import typing
from datetime import datetime, timedelta
from enum import Enum

from line.test import TestCommonEvent, TestRunEvent, TestOutputEvent, TestPassEvent, TestFailEvent, TestEvent, \
    TestContinueEvent, TestPauseEvent, TestSkipEvent


class Status(Enum):
    Unknown = 1
    Fail = 2
    Pass = 3
    Skip = 4


class Run(object):
    name:   str
    status: Status
    output: typing.List[str]

    paused:    float
    paused_at: typing.Optional[datetime]

    started_at:  datetime
    finished_at: datetime
    elapsed:     float

    def __init__(self, name: str):
        self.name = name
        self.status = Status.Unknown
        self.output = list()

        self.paused = 0
        self.paused_at = None

        self.started_at = None
        self.finished_at = None
        self.elapsed = 0

    def is_finished(self) -> bool:
        return self.status is not Status.Unknown

    def is_paused(self) -> bool:
        return self.paused_at is not None

    def is_failed(self) -> typing.Optional[bool]:
        if self.status == Status.Unknown:
            for line in self.output:
                if "--- PASS:" in line:
                    return False
                elif "--- FAIL:" in line:
                    return True
            return None
        return self.status == Status.Fail

    def is_skipped(self) -> bool:
        return self.status == Status.Skip


class TestIsNotInitialized(Exception):
    pass


class TestIsFinished(Exception):
    pass


class TestAlreadyPaused(Exception):
    pass


class TestIsPaused(Exception):
    pass


class Test(object):
    name: str
    runs: typing.List[Run]

    def __init__(self, name: str):
        self.name = name
        self.runs = list()

    def last_run(self) -> Run:
        return self.runs[len(self.runs) - 1]

    def add_event(self, event: TestEvent):
        if len(self.runs) == 0:
            if not isinstance(event, TestRunEvent):
                raise TestIsNotInitialized()
        elif self.last_run().is_finished() is True:
            if not isinstance(event, TestRunEvent):
                raise TestIsFinished()
        elif self.last_run().is_paused() is True:
            if isinstance(event, TestPauseEvent):
                raise TestAlreadyPaused()
            elif not isinstance(event, TestContinueEvent):
                raise TestIsPaused()

        if isinstance(event, TestRunEvent):
            self.runs.append(Run(self.name))
        elif isinstance(event, TestPauseEvent):
            self.last_run().paused_at = event.time
        elif isinstance(event, TestContinueEvent):
            last_run = self.last_run()
            last_run.paused += (event.time - last_run.paused_at) / timedelta(days=1)
            last_run.paused_at = None
        elif isinstance(event, TestPassEvent):
            last_run = self.last_run()
            last_run.status = Status.Pass
            last_run.finished_at = event.time
        elif isinstance(event, TestFailEvent):
            last_run = self.last_run()
            last_run.status = Status.Fail
            last_run.finished_at = event.time
        elif isinstance(event, TestOutputEvent):
            self.last_run().output.append(event.message.strip())
        elif isinstance(event, TestSkipEvent):
            last_run = self.last_run()
            last_run.status = Status.Skip
            last_run.finished_at = event.time
            last_run.elapsed = event.elapsed
        else:
            raise NotImplementedError()


class PackageAlreadyFinished(Exception):
    pass


class Package(object):
    name:    str
    output:  typing.List[str]
    tests:   typing.Dict[str, Test]
    status:  Status
    elapsed: float

    def __init__(self, name):
        self.name = name
        self.output = list()
        self.tests = dict()
        self.status = Status.Unknown
        self.elapsed = 0

    def add_event(self, event: TestEvent):
        if isinstance(event, TestFailEvent):
            self.status = Status.Fail
            self.elapsed = event.elapsed
        elif isinstance(event, TestPassEvent) and event.test is not None:
            self.status = Status.Pass
            self.elapsed = event.elapsed
        elif isinstance(event, TestRunEvent):
            test = self.obtain_test(event.test, False)
            test.add_event(event)
        elif isinstance(event, TestOutputEvent):
            test_name = event.test
            if test_name is None:
                self.output.append(event.message.strip())
            else:
                test = self.obtain_test(test_name, True)
                test.add_event(event)
        else:
            test_name = event.test
            test = self.obtain_test(test_name, True)
            test.add_event(event)

    def obtain_test(self, test_name: str, required: bool) -> Test:
        if test_name not in self.tests:
            if required:
                raise NotImplementedError()
            self.tests[test_name] = Test(test_name)
        return self.tests[test_name]


class OverallInformation(object):
    package_list: typing.Dict[str, Package]

    def __init__(self):
        self.package_list = dict()

    def obtain_package(self, package_name):
        if package_name not in self.package_list:
            self.package_list[package_name] = Package(package_name)
        return self.package_list[package_name]

    def add_event(self, event: TestEvent):
        package = self.obtain_package(event.package)
        package.add_event(event)

    def brief_failed(self) -> typing.List[Run]:
        rv = list()
        for package_name, package in self.package_list.items():
            for test in package.tests.values():
                for run in test.runs:
                    if run.is_failed():
                        rv.append(run)
        return rv

