import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.plot import Plot


# ---------------------------------------------------------------------------
# Concrete test implementation
# ---------------------------------------------------------------------------

class TimeSeriesPlot(Plot):
    """Renders one or more named signals against time in seconds."""

    def render(self, result: AnalysisResult) -> plt.Figure:
        timestamps_s = [t / 1e6 for t in result.timestamps_us]
        self._data = {
            "timestamps_s": timestamps_s,
            "signals": {k: list(v) for k, v in result.signals.items()},
        }
        fig, ax = plt.subplots()
        for name, values in result.signals.items():
            ax.plot(timestamps_s, values, label=name)
        ax.legend()
        return fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(n: int = 5, **signal_factories) -> AnalysisResult:
    """Build an AnalysisResult with n samples. signal_factories: name → callable(i)."""
    if not signal_factories:
        signal_factories = {"value": float}
    result = AnalysisResult()
    for i in range(n):
        kwargs = {name: fn(i) for name, fn in signal_factories.items()}
        result.add_sample(i * 1_000_000, **kwargs)  # 1-second steps
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_data_empty_before_render():
    plot = TimeSeriesPlot()
    assert plot.get_data() == {}


def test_render_returns_figure():
    result = make_result(3)
    plot = TimeSeriesPlot()
    fig = plot.render(result)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_get_data_timestamps_in_seconds():
    result = make_result(3)
    plot = TimeSeriesPlot()
    plot.render(result)
    assert plot.get_data()["timestamps_s"] == pytest.approx([0.0, 1.0, 2.0])


def test_get_data_signal_values():
    result = make_result(3, speed=lambda i: float(i * 2))
    plot = TimeSeriesPlot()
    plot.render(result)
    assert plot.get_data()["signals"]["speed"] == [0.0, 2.0, 4.0]


def test_get_data_multiple_signals():
    result = make_result(2, x=lambda i: float(i), y=lambda i: float(i * 10))
    plot = TimeSeriesPlot()
    plot.render(result)
    data = plot.get_data()
    assert data["signals"]["x"] == [0.0, 1.0]
    assert data["signals"]["y"] == [0.0, 10.0]


def test_render_is_idempotent():
    result = make_result(2)
    plot = TimeSeriesPlot()
    fig1 = plot.render(result)
    data1 = dict(plot.get_data())
    fig2 = plot.render(result)
    data2 = dict(plot.get_data())
    assert data1["timestamps_s"] == data2["timestamps_s"]
    plt.close(fig1)
    plt.close(fig2)


def test_empty_result_renders_without_error():
    result = AnalysisResult()
    plot = TimeSeriesPlot()
    fig = plot.render(result)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
