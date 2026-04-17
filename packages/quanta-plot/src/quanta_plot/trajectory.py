from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.plot import Plot


def _quiver_normalized(ax, x, y, vx, vy, **kwargs) -> None:
    """Draw unit-direction arrows at fixed visual size (~6 dots, ≈2× a markersize-3 circle)."""
    arr_vx = np.asarray(vx, dtype=float)
    arr_vy = np.asarray(vy, dtype=float)
    mag = np.hypot(arr_vx, arr_vy)
    safe = np.where(mag > 0, mag, 1.0)
    ax.quiver(x, y, arr_vx / safe, arr_vy / safe,
              color="green",
              angles="xy", units="dots",
              scale=1 / 6, width=1.5, headwidth=4, headlength=5,
              zorder=2, **kwargs)


class CartesianTrajectoryPlot(Plot):
    def render(self, result: AnalysisResult) -> plt.Figure:
        x  = result.signals.get("x", [])
        y  = result.signals.get("y", [])
        vx = result.signals.get("vx", [0.0] * len(x))
        vy = result.signals.get("vy", [0.0] * len(y))

        self._data = {"x": x, "y": y, "vx": vx, "vy": vy}

        fig, ax = plt.subplots()
        if x:
            _quiver_normalized(ax, x, y, vx, vy)
        ax.plot(x, y, "-o", markersize=3, label="path", zorder=3)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_aspect("equal")
        ax.legend()
        return fig
