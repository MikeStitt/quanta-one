from typing import Any, Iterator

from pykit.logtable import LogTable
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
