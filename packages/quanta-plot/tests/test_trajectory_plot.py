import matplotlib.pyplot as plt
import pytest

from quanta_analysis.analyzer import AnalysisResult
from quanta_plot.trajectory import CartesianTrajectoryPlot


def _make_result(n: int = 3) -> AnalysisResult:
    result = AnalysisResult()
    for i in range(n):
        result.add_sample(i * 1000, x=float(i), y=float(i), vx=1.0, vy=0.0)
    return result


def test_render_returns_figure():
    fig = CartesianTrajectoryPlot().render(_make_result())
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_get_data_has_xy():
    plot = CartesianTrajectoryPlot()
    plot.render(_make_result())
    data = plot.get_data()
    assert "x" in data
    assert "y" in data
    plt.close("all")


def test_velocity_in_get_data():
    plot = CartesianTrajectoryPlot()
    plot.render(_make_result())
    data = plot.get_data()
    assert "vx" in data
    assert "vy" in data
    plt.close("all")


def test_empty_result_no_crash():
    fig = CartesianTrajectoryPlot().render(AnalysisResult())
    assert isinstance(fig, plt.Figure)
    plt.close("all")
