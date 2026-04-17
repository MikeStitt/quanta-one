from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from pykit.logtable import LogTable

from quanta_analysis.analyzer import Analyzer, AnalysisResult

if TYPE_CHECKING:
    from quanta_io.signal import LogSignalMap


class PoseTrajectoryAnalyzer(Analyzer):
    def __init__(self, pose_key: str) -> None:
        self._pose_key = pose_key

    def process(self, tables: Iterable[LogTable]) -> AnalysisResult:
        from quanta_io.log_source import build_signal_map
        return self.process_signals(build_signal_map(tables))

    def process_signals(self, log_map: "LogSignalMap") -> AnalysisResult:
        if self._pose_key not in log_map:
            return AnalysisResult()

        sig = log_map[self._pose_key]

        if not sig.values:
            return AnalysisResult()

        raw_ts = sig.timestamps_us
        raw_x = [pose.translation().X() for pose in sig.values]
        raw_y = [pose.translation().Y() for pose in sig.values]

        # Drop exact-origin frames — (0.0, 0.0) means the pose estimator hasn't
        # converged yet and produces a spurious multi-meter jump on the first real fix.
        valid = [(t, px, py) for t, px, py in zip(raw_ts, raw_x, raw_y)
                 if not (px == 0.0 and py == 0.0)]
        if not valid:
            return AnalysisResult()
        timestamps, x, y = map(list, zip(*valid))

        n = len(x)
        vx = [x[i + 1] - x[i] for i in range(n - 1)] + [0.0]
        vy = [y[i + 1] - y[i] for i in range(n - 1)] + [0.0]

        result = AnalysisResult()
        for i, ts in enumerate(timestamps):
            result.add_sample(ts, x=x[i], y=y[i], vx=vx[i], vy=vy[i])

        return result
