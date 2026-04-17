from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections.abc import KeysView


@dataclass
class LogSignal:
    name: str
    type_str: str  # "double", "struct:Pose2d", etc.
    timestamps_us: list[int] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)


class LogSignalMap:
    def __init__(self, signals: dict[str, LogSignal]) -> None:
        self._signals = signals

    def __getitem__(self, name: str) -> LogSignal:
        return self._signals[name]

    def __contains__(self, name: object) -> bool:
        return name in self._signals

    def keys(self) -> KeysView[str]:
        return self._signals.keys()

    def field_names(self) -> list[str]:
        """All keys excluding those starting with '.schema/'."""
        return [k for k in self._signals if not k.startswith(".schema/")]
