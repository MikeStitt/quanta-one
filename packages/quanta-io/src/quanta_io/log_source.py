from typing import Any, Iterable, Iterator

from pykit.logtable import LogTable
from pykit.logvalue import LogValue
from pykit.wpilog.wpilogreader import WPILOGReader


class WPILogFileSource:
    """Iterates a PyKit-generated .wpilog file as a sequence of LogTable snapshots."""

    def __init__(self, filename: str) -> None:
        self._filename = filename

    def __iter__(self) -> Iterator[LogTable]:
        reader = WPILOGReader(self._filename)
        reader.start()
        table = LogTable(0)
        while reader.updateTable(table):
            yield LogTable.clone(table)
        reader.end()


class MockLogSource:
    """
    In-memory log source for testing without .wpilog files.

    Each frame is a dict with:
      - ``timestamp_us``: int timestamp in microseconds
      - ``values``: dict[str, Any] of key→value pairs passed to LogTable.put()
    """

    def __init__(self, frames: list[dict[str, Any]]) -> None:
        self._frames = frames

    def __iter__(self) -> Iterator[LogTable]:
        for frame in self._frames:
            table = LogTable(frame["timestamp_us"])
            for key, value in frame.get("values", {}).items():
                table.put(key, value)
            yield table


def build_signal_map(
    tables: Iterable[LogTable],
    registry=None,
):
    """Pivot Iterable[LogTable] → LogSignalMap.

    Strips leading '/' from keys; skips '.schema/' entries; decodes known structs.
    """
    from quanta_io.signal import LogSignal, LogSignalMap
    from quanta_io.struct_registry import default_registry

    if registry is None:
        registry = default_registry

    signals: dict[str, LogSignal] = {}

    for table in tables:
        ts = table.getTimestamp()
        for raw_key, log_value in table.getAll().items():
            key = raw_key.lstrip("/")
            if key.startswith(".schema/"):
                continue

            if key not in signals:
                signals[key] = LogSignal(name=key, type_str=log_value.getWPILOGType())
            signal = signals[key]

            if (
                log_value.log_type == LogValue.LoggableType.Raw
                and log_value.custom_type.startswith("struct:")
            ):
                if registry.can_decode(log_value.custom_type):
                    value = registry.decode(log_value.custom_type, log_value.value)
                else:
                    value = log_value.value
            else:
                value = log_value.value

            signal.timestamps_us.append(ts)
            signal.values.append(value)

    return LogSignalMap(signals)


def read_wpilog_signals(path: str, registry=None):
    """Read a PyKit-generated .wpilog file directly into a LogSignalMap."""
    return build_signal_map(WPILogFileSource(path), registry)
