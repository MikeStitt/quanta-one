from typing import Iterable, Optional

import numpy as np

from pykit.logtable import LogTable

from quanta_analysis.analyzer import Analyzer, AnalysisResult


class SwerveOdometryVarianceAnalyzer(Analyzer):
    """
    Computes rolling variance of swerve drive odometry (and optionally vision) pose signals.

    For each signal, variance is computed over a sliding window of ``window`` samples using
    numpy. Samples with fewer than 2 values in the window produce NaN.

    :param odom_x_key: Full log key for odometry X (e.g. "/Drive/OdometryX").
    :param odom_y_key: Full log key for odometry Y.
    :param vision_x_key: Optional full log key for vision X.
    :param vision_y_key: Optional full log key for vision Y.
    :param window: Rolling window size in samples (default 50).
    """

    def __init__(
        self,
        odom_x_key: str,
        odom_y_key: str,
        vision_x_key: Optional[str] = None,
        vision_y_key: Optional[str] = None,
        window: int = 50,
    ) -> None:
        self._odom_x_key = odom_x_key
        self._odom_y_key = odom_y_key
        self._vision_x_key = vision_x_key
        self._vision_y_key = vision_y_key
        self._window = window

    def process(self, tables: Iterable[LogTable]) -> AnalysisResult:
        timestamps: list[int] = []
        odom_x: list[float] = []
        odom_y: list[float] = []
        vision_x: list[float] = []
        vision_y: list[float] = []

        has_vision = self._vision_x_key is not None and self._vision_y_key is not None

        for table in tables:
            timestamps.append(table.getTimestamp())
            odom_x.append(table.getDouble(self._odom_x_key, 0.0))
            odom_y.append(table.getDouble(self._odom_y_key, 0.0))
            if has_vision:
                vision_x.append(table.getDouble(self._vision_x_key, 0.0))
                vision_y.append(table.getDouble(self._vision_y_key, 0.0))

        if not timestamps:
            return AnalysisResult()

        odom_x_var = self._rolling_var(odom_x)
        odom_y_var = self._rolling_var(odom_y)

        vision_x_var = self._rolling_var(vision_x) if has_vision else None
        vision_y_var = self._rolling_var(vision_y) if has_vision else None

        result = AnalysisResult()
        for i, ts in enumerate(timestamps):
            kwargs: dict = {
                "odom_x_var": odom_x_var[i],
                "odom_y_var": odom_y_var[i],
            }
            if has_vision:
                kwargs["vision_x_var"] = vision_x_var[i]
                kwargs["vision_y_var"] = vision_y_var[i]
            result.add_sample(ts, **kwargs)

        return result

    def _rolling_var(self, values: list[float]) -> np.ndarray:
        arr = np.array(values, dtype=float)
        n = len(arr)
        result = np.full(n, np.nan)
        for i in range(n):
            start = max(0, i - self._window + 1)
            window_vals = arr[start : i + 1]
            if len(window_vals) >= 2:
                result[i] = np.var(window_vals, ddof=1)
            elif len(window_vals) == 1:
                result[i] = 0.0
        return result
