import pytest

from pykit.logtable import LogTable
from pykit.logvalue import LogValue

from quanta_io.log_source import MockLogSource, build_signal_map
from quanta_io.signal import LogSignal, LogSignalMap
from quanta_io.struct_registry import StructTypeRegistry


def test_empty_source_returns_empty_map():
    log_map = build_signal_map(MockLogSource([]))
    assert len(log_map.field_names()) == 0


def test_double_signal_decoded():
    source = MockLogSource([{"timestamp_us": 1000, "values": {"x": 1.5}}])
    log_map = build_signal_map(source)
    signal = log_map["x"]
    assert isinstance(signal.values[0], float)
    assert signal.values[0] == pytest.approx(1.5)


def test_timestamps_correct():
    source = MockLogSource([
        {"timestamp_us": 1000, "values": {"x": 1.0}},
        {"timestamp_us": 2000, "values": {"x": 2.0}},
    ])
    log_map = build_signal_map(source)
    assert log_map["x"].timestamps_us == [1000, 2000]


def test_schema_entries_excluded():
    table = LogTable(1000)
    table.data["/.schema/struct:Foo"] = LogValue.withType(
        LogValue.LoggableType.Raw, b"schema", "structschema"
    )
    table.put("x", 1.0)
    log_map = build_signal_map([table])
    assert ".schema/struct:Foo" not in log_map.field_names()
    assert "x" in log_map.field_names()


def test_unknown_struct_stored_as_bytes():
    raw = b"\x00" * 48
    table = LogTable(1000)
    table.putValue("sensor", LogValue.withType(LogValue.LoggableType.Raw, raw, "struct:Unknown"))
    registry = StructTypeRegistry()  # empty — can't decode "struct:Unknown"
    log_map = build_signal_map([table], registry=registry)
    assert log_map["sensor"].values[0] == raw


def test_signal_contains():
    source = MockLogSource([{"timestamp_us": 500, "values": {"speed": 3.0}}])
    log_map = build_signal_map(source)
    assert "speed" in log_map
    assert "missing" not in log_map
