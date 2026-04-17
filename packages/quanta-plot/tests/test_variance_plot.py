import matplotlib.pyplot as plt
import pytest

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.variance import VarianceTimeSeriesPlot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(**signal_factories) -> AnalysisResult:
    result = AnalysisResult()
    for i in range(5):
        kwargs = {name: fn(i) for name, fn in signal_factories.items()}
        result.add_sample(i * 1_000_000, **kwargs)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_data_empty_before_render():
    plot = VarianceTimeSeriesPlot()
    assert plot.get_data() == {}


def test_render_returns_figure():
    result = make_result(odom_x_var=float)
    plot = VarianceTimeSeriesPlot()
    fig = plot.render(result)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_timestamps_s_correct():
    result = make_result(odom_x_var=float)
    plot = VarianceTimeSeriesPlot()
    plot.render(result)
    assert plot.get_data()["timestamps_s"] == pytest.approx([0.0, 1.0, 2.0, 3.0, 4.0])


def test_all_signals_present_in_get_data():
    result = make_result(
        odom_x_var=lambda i: float(i),
        odom_y_var=lambda i: float(i * 2),
    )
    plot = VarianceTimeSeriesPlot()
    plot.render(result)
    data = plot.get_data()
    assert "odom_x_var" in data["signals"]
    assert "odom_y_var" in data["signals"]
    assert data["signals"]["odom_x_var"] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert data["signals"]["odom_y_var"] == [0.0, 2.0, 4.0, 6.0, 8.0]


def test_empty_result_renders_without_error():
    result = AnalysisResult()
    plot = VarianceTimeSeriesPlot()
    fig = plot.render(result)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_empty_timestamps_s_for_empty_result():
    result = AnalysisResult()
    plot = VarianceTimeSeriesPlot()
    plot.render(result)
    assert plot.get_data()["timestamps_s"] == []
