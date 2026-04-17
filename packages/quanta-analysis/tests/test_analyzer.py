from typing import Iterable

import pytest

from pykit.logtable import LogTable
from quanta_analysis.analyzer import Analyzer, AnalysisResult


# ---------------------------------------------------------------------------
# Concrete test implementation
# ---------------------------------------------------------------------------

class SignalExtractor(Analyzer):
    """Extracts a single named double signal from each LogTable."""

    def __init__(self, key: str, default: float = 0.0) -> None:
        self._key = key
        self._default = default

    def process(self, tables: Iterable[LogTable]) -> AnalysisResult:
        result = AnalysisResult()
        for table in tables:
            value = table.getDouble(self._key, self._default)
            result.add_sample(table.getTimestamp(), value=value)
        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tables(data: list[tuple[int, float]], key: str) -> list[LogTable]:
    tables = []
    for ts, val in data:
        t = LogTable(ts)
        t.put(key, val)
        tables.append(t)
    return tables


# ---------------------------------------------------------------------------
# AnalysisResult tests
# ---------------------------------------------------------------------------

def test_add_sample_timestamps():
    result = AnalysisResult()
    result.add_sample(1000, x=1.0)
    result.add_sample(2000, x=2.0)
    assert result.timestamps_us == [1000, 2000]


def test_add_sample_multiple_signals():
    result = AnalysisResult()
    result.add_sample(1000, x=1.0, y=2.0)
    result.add_sample(2000, x=3.0, y=4.0)
    assert result.signals["x"] == [1.0, 3.0]
    assert result.signals["y"] == [2.0, 4.0]


def test_add_sample_creates_signal_on_first_use():
    result = AnalysisResult()
    result.add_sample(1000, new_signal=42.0)
    assert "new_signal" in result.signals
    assert result.signals["new_signal"] == [42.0]


def test_empty_result():
    result = AnalysisResult()
    assert result.timestamps_us == []
    assert result.signals == {}


# ---------------------------------------------------------------------------
# Analyzer tests
# ---------------------------------------------------------------------------

def test_extractor_timestamps():
    tables = make_tables([(1000, 1.0), (2000, 2.0), (3000, 3.0)], "speed")
    result = SignalExtractor("speed").process(tables)
    assert result.timestamps_us == [1000, 2000, 3000]


def test_extractor_signal_values():
    tables = make_tables([(1000, 5.0), (2000, 10.0)], "speed")
    result = SignalExtractor("speed").process(tables)
    assert result.signals["value"] == [5.0, 10.0]


def test_extractor_missing_key_uses_default():
    tables = make_tables([(1000, 1.0)], "other_key")
    result = SignalExtractor("speed", default=-1.0).process(tables)
    assert result.signals["value"] == [-1.0]


def test_extractor_empty_stream():
    result = SignalExtractor("speed").process([])
    assert result.timestamps_us == []
    assert result.signals == {}


def test_extractor_single_frame():
    tables = make_tables([(500, 3.14)], "val")
    result = SignalExtractor("val").process(tables)
    assert len(result.timestamps_us) == 1
    assert result.signals["value"][0] == pytest.approx(3.14)
