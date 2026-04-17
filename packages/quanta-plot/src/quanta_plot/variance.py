import matplotlib.pyplot as plt

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.plot import Plot


class VarianceTimeSeriesPlot(Plot):
    """
    Plots each signal in an AnalysisResult as a variance time-series.

    X-axis is time in seconds (converted from microseconds).
    Each signal gets its own line labeled by signal name.
    """

    def render(self, result: AnalysisResult) -> plt.Figure:
        timestamps_s = [t / 1e6 for t in result.timestamps_us]
        self._data = {
            "timestamps_s": timestamps_s,
            "signals": {k: list(v) for k, v in result.signals.items()},
        }
        fig, ax = plt.subplots()
        for name, values in result.signals.items():
            ax.plot(timestamps_s, values, label=name)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Variance")
        if result.signals:
            ax.legend()
        return fig
