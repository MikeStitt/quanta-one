import pytest

from quanta_analysis.pose_trajectory import PoseTrajectoryAnalyzer
from quanta_io.signal import LogSignal, LogSignalMap


class _MockTranslation:
    def __init__(self, x: float, y: float) -> None:
        self._x, self._y = x, y

    def X(self) -> float:
        return self._x

    def Y(self) -> float:
        return self._y


class _MockPose2d:
    def __init__(self, x: float, y: float) -> None:
        self._t = _MockTranslation(x, y)

    def translation(self) -> _MockTranslation:
        return self._t


def _make_log_map(xy_pairs: list[tuple[float, float]], timestamps: list[int] | None = None) -> LogSignalMap:
    if timestamps is None:
        timestamps = list(range(len(xy_pairs)))
    poses = [_MockPose2d(x, y) for x, y in xy_pairs]
    signal = LogSignal(
        name="Robot/Pose",
        type_str="struct:Pose2d",
        timestamps_us=timestamps,
        values=poses,
    )
    return LogSignalMap({"Robot/Pose": signal})


def test_origin_frames_filtered_out():
    # Leading (0, 0) frame should be dropped so it doesn't produce a spurious jump arrow
    log_map = _make_log_map([(0.0, 0.0), (1.0, 2.0), (3.0, 4.0)], timestamps=[0, 1000, 2000])
    result = PoseTrajectoryAnalyzer("Robot/Pose").process_signals(log_map)
    assert result.signals["x"][0] == pytest.approx(1.0), "origin frame should be filtered"
    assert len(result.timestamps_us) == 2


def test_empty_map_returns_empty_result():
    analyzer = PoseTrajectoryAnalyzer("Robot/Pose")
    result = analyzer.process_signals(LogSignalMap({}))
    assert result.timestamps_us == []


def test_xy_extracted_correctly():
    log_map = _make_log_map([(1.0, 2.0), (3.0, 4.0)], timestamps=[1000, 2000])
    result = PoseTrajectoryAnalyzer("Robot/Pose").process_signals(log_map)
    assert result.signals["x"] == pytest.approx([1.0, 3.0])
    assert result.signals["y"] == pytest.approx([2.0, 4.0])


def test_velocity_vectors_point_to_next():
    log_map = _make_log_map([(1.0, 0.0), (2.0, 2.0), (4.0, 5.0)], timestamps=[0, 1, 2])
    result = PoseTrajectoryAnalyzer("Robot/Pose").process_signals(log_map)
    assert result.signals["vx"][0] == pytest.approx(2.0 - 1.0)
    assert result.signals["vy"][0] == pytest.approx(2.0 - 0.0)


def test_last_point_velocity_is_zero():
    log_map = _make_log_map([(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)], timestamps=[0, 1, 2])
    result = PoseTrajectoryAnalyzer("Robot/Pose").process_signals(log_map)
    assert result.signals["vx"][-1] == pytest.approx(0.0)
    assert result.signals["vy"][-1] == pytest.approx(0.0)


def test_timestamps_preserved():
    timestamps = [1000, 2000, 3000]
    log_map = _make_log_map([(1.0, 0.0), (2.0, 0.0), (3.0, 0.0)], timestamps=timestamps)
    result = PoseTrajectoryAnalyzer("Robot/Pose").process_signals(log_map)
    assert result.timestamps_us == timestamps
