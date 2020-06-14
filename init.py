import collections
import os
import subprocess
import typing

from lib.filter import FilterOptions, NewDefaultFilter
from line.log import LogLine
from input.log import SingleReader


def find_executable(name: typing.AnyStr) -> typing.AnyStr:
    for path in os.get_exec_path():
        binary_path = os.path.join(path, name)
        if os.path.exists(binary_path):
            return binary_path

    return None


def find_logfiles(path: typing.AnyStr) -> typing.List[typing.AnyStr]:
    loglist = []

    for root, dirs, files in os.walk(os.path.abspath(path), topdown=True):
        for fl in files:
            if not fl.endswith(".log"):
                continue
            filename = os.path.join(root, fl)
            loglist.append(filename)

    return loglist


class TraceIDStats(object):
    def __init__(self, trace_id: str, line_filter: FilterOptions):
        self.trace_id = trace_id
        self.filter = line_filter

        self.count = 0
        self.last_message_time = None
        self.last_message = ""

        self.call_site = None

    def add_message(self, line: LogLine):
        self.count += 1

        message = line.message
        if self.last_message_time is None or self.last_message_time < line.timestamp:
            self.last_message_time = line.timestamp
            self.last_message = message

        if self.call_site is None and message.find("Incoming request") > -1:
            self.call_site = line.fields.get("callSite", None)

    def __repr__(self):
        return "(%s, %s, '%s')" % (self.trace_id, self.count, self.last_message)


class TraceIDList(object):
    trace_ids: typing.Mapping[str, TraceIDStats]
    trace_ids_banned: typing.Mapping[str, bool]

    def __init__(self):
        self.line_filter = NewDefaultFilter()
        self.trace_ids = {}
        self.trace_ids_banned = {}

    def read_log_files(self, log_files):
        for logfile in sorted(log_files):
            self.read_log_file(logfile)

    def read_log_file(self, log_file: str):
        print("> Processing file '%s'" % log_file)
        r = SingleReader(open(log_file, 'r'), self.line_filter)
        for line in r.read_generator():
            self.line_append(line)

    def line_append(self, line: LogLine):
        if self.line_filter.filter_log_line(line):
            return

        trace_id = line.traceid
        if trace_id is None or trace_id in self.trace_ids_banned:
            return

        if trace_id not in self.trace_ids:
            self.trace_ids[trace_id] = TraceIDStats(trace_id, self.line_filter)

        self.trace_ids[trace_id].add_message(line)

        pass

    def cleanup(self):
        to_delete_list = []
        for trace_id, stat in self.trace_ids.items():
            if stat.call_site is None and not trace_id.startswith("object-"):
                to_delete_list.append(trace_id)

        for to_delete in to_delete_list:
            del self.trace_ids[to_delete]


def print_debug(trace_id_list: TraceIDList):
    object_list = dict()
    t = collections.defaultdict(dict)
    for trace_id, stat in trace_id_list.trace_ids.items():
        if stat.call_site is not None:
            t[stat.call_site][trace_id] = stat
        else:
            object_list[trace_id] = stat

    for call_site, trace_id_map in t.items():
        print("==== %s" % call_site)
        for stat in sorted(trace_id_map.values(), key=lambda x: x.count):
            print("  %s" % repr(stat))
        print("")

    for _, stat in sorted(object_list.items(), key=lambda x: x[0]):
        print(repr(stat))


def collect_logs(trace_id_list: TraceIDList, input_dir: str):
    out_request_tpl = "/tmp/1/%s-%s.%s.trace"
    out_object_tpl = "/tmp/1/%s.trace"
    cmd_tpl = """ag --nofilename %s %s | jq -s -c 'sort_by(.time) | .[]'"""
    cmd_to_read_tpl = """cat '%s' | python3 /data/python/traceidextractor/logparse.py --force-color | less -SRq"""

    for trace_id, stat in trace_id_list.trace_ids.items():
        if stat.call_site is not None:
            out_name = out_request_tpl % (stat.call_site, stat.count, trace_id)
        else:
            out_name = out_object_tpl % trace_id

        cmd = cmd_tpl % (trace_id, input_dir)

        with open(out_name, "w") as out:
            p = subprocess.Popen(cmd, stdout=out, stderr=subprocess.PIPE, shell=True)
            _, stderr = p.communicate(None)
            if p.returncode != 0:
                print("Failed to execute '%s': %s" % (cmd, stderr))
                return
            else:
                cmd_to_read = cmd_to_read_tpl % out_name
                print("To read use '%s'" % cmd_to_read)


def main():
    input_dir = "/data/go/src/github.com/insolar/insolar/.artifacts/launchnet/logs/discoverynodes/"
    logs = find_logfiles(input_dir)

    trace_id_list = TraceIDList()
    trace_id_list.read_log_files(logs)
    trace_id_list.cleanup()

    print_debug(trace_id_list)
    collect_logs(trace_id_list, input_dir)


if __name__ == "__main__":
    main()
