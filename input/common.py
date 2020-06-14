import typing
from collections import defaultdict

JSONObjectKeyValueList = typing.NewType("JSONObjectKeyValueList", typing.Collection[typing.Dict[str, typing.Any]])
JSONObject = typing.NewType("JSONObject", typing.Dict[str, typing.Collection[str]])


def json_object_multiple(inp: JSONObjectKeyValueList) -> JSONObject:
    out = dict()
    for (key, value) in inp:
        if key in out:
            if isinstance(out[key], list):
                out[key].append(value)
            else:
                out[key] = list([out[key], value])
        else:
            out[key] = value

    new_out = dict()
    for key, value in out.items():
        if isinstance(value, list) and len(value) == 1:
            new_out[key] = value.pop()
        else:
            new_out[key] = value

    return new_out


def json_object_multiple_unique(inp: JSONObjectKeyValueList) -> JSONObject:
    out: typing.DefaultDict[str, typing.Set[typing.Any]] = defaultdict(set)
    for (key, value) in inp:
        out[key].add(value)

    new_out: typing.Dict[str, typing.Any] = {}
    for key, value in out.items():
        if len(value) == 1:
            new_out[key] = value.pop()
        else:
            new_out[key] = list(value)

    return new_out


