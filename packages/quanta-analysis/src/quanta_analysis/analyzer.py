from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from pykit.logtable import LogTable


@dataclass
class AnalysisResult:
    """Holds timestamped output signals produced by an Analyzer."""

    timestamps_us: list[int] = field(default_factory=list)
    signals: dict[str, list] = field(default_factory=dict)

    def add_sample(self, timestamp_us: int, **kwargs) -> None:
        """
        Append one sample across all named signals.

        :param timestamp_us: Timestamp in microseconds.
        :param kwargs: Signal name → value pairs.
        """
        self.timestamps_us.append(timestamp_us)
        for key, value in kwargs.items():
            self.signals.setdefault(key, []).append(value)


class Analyzer(ABC):
    """
    Base class for all quanta analyzers.

    Subclasses implement ``process()`` to consume a stream of LogTable snapshots
    and return an AnalysisResult containing derived signals.
    """

    @abstractmethod
    def process(self, tables: Iterable[LogTable]) -> AnalysisResult:
        """
        Process a stream of LogTable snapshots and return analysis results.

        :param tables: Iterable of LogTable snapshots (e.g. from WPILogFileSource or MockLogSource).
        :return: AnalysisResult with timestamps and named signal arrays.
        """
        ...
