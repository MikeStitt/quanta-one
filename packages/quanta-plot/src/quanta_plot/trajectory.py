from __future__ import annotations

import matplotlib.pyplot as plt

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.plot import Plot


class CartesianTrajectoryPlot(Plot):
    def render(self, result: AnalysisResult) -> plt.Figure:
        x = result.signals.get("x", [])
        y = result.signals.get("y", [])
        vx = result.signals.get("vx", [0.0] * len(x))
        vy = result.signals.get("vy", [0.0] * len(y))

        self._data = {"x": x, "y": y, "vx": vx, "vy": vy}

        fig, ax = plt.subplots()
        ax.plot(x, y, "-o", markersize=3, label="path")
        if x:
            ax.quiver(x, y, vx, vy, angles="xy", scale_units="xy", scale=1)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_aspect("equal")
        ax.legend()
        return fig
