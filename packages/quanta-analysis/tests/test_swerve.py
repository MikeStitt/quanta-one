import math

import pytest

from pykit.logtable import LogTable

from quanta_analysis.swerve import SwerveOdometryVarianceAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tables(odom_x: list[float], odom_y: list[float]) -> list[LogTable]:
    tables = []
    for i, (x, y) in enumerate(zip(odom_x, odom_y)):
        t = LogTable(i * 1_000_000)
        t.put("Drive/OdometryX", x)
        t.put("Drive/OdometryY", y)
        tables.append(t)
    return tables


def make_analyzer(**kwargs) -> SwerveOdometryVarianceAnalyzer:
    return SwerveOdometryVarianceAnalyzer(
        "Drive/OdometryX", "Drive/OdometryY", **kwargs
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_stream_returns_empty_result():
    result = make_analyzer().process([])
    assert result.timestamps_us == []
    assert result.signals == {}


def test_constant_signal_variance_is_zero():
    tables = make_tables([5.0] * 10, [3.0] * 10)
    result = make_analyzer(window=5).process(tables)
    # After window fills, variance of constant is 0
    for v in result.signals["odom_x_var"][4:]:
        assert v == pytest.approx(0.0, abs=1e-9)


def test_varying_signal_has_nonzero_variance():
    odom_x = [float(i) for i in range(20)]
    tables = make_tables(odom_x, [0.0] * 20)
    result = make_analyzer(window=5).process(tables)
    # After first full window, variance of linearly increasing signal is > 0
    assert result.signals["odom_x_var"][4] > 0.0


def test_timestamps_preserved():
    tables = make_tables([1.0, 2.0, 3.0], [0.0, 0.0, 0.0])
    result = make_analyzer().process(tables)
    assert result.timestamps_us == [0, 1_000_000, 2_000_000]


def test_no_vision_keys_in_result_when_not_provided():
    tables = make_tables([1.0, 2.0], [0.0, 0.0])
    result = make_analyzer().process(tables)
    assert "vision_x_var" not in result.signals
    assert "vision_y_var" not in result.signals


def test_vision_keys_present_when_provided():
    tables = []
    for i in range(5):
        t = LogTable(i * 1_000_000)
        t.put("Drive/OdometryX", float(i))
        t.put("Drive/OdometryY", float(i))
        t.put("Vision/PoseX", float(i) * 2)
        t.put("Vision/PoseY", float(i) * 2)
        tables.append(t)

    analyzer = SwerveOdometryVarianceAnalyzer(
        "Drive/OdometryX", "Drive/OdometryY",
        vision_x_key="Vision/PoseX", vision_y_key="Vision/PoseY",
        window=3,
    )
    result = analyzer.process(tables)
    assert "vision_x_var" in result.signals
    assert "vision_y_var" in result.signals


def test_window_larger_than_data_does_not_crash():
    tables = make_tables([1.0, 2.0], [0.0, 0.0])
    result = make_analyzer(window=100).process(tables)
    # Single-sample window → var=0; two-sample window → var > 0
    assert len(result.signals["odom_x_var"]) == 2
    assert result.signals["odom_x_var"][0] == pytest.approx(0.0)
    assert result.signals["odom_x_var"][1] > 0.0


def test_single_frame_variance_is_zero():
    tables = make_tables([7.5], [2.1])
    result = make_analyzer().process(tables)
    assert len(result.timestamps_us) == 1
    assert result.signals["odom_x_var"][0] == pytest.approx(0.0)
