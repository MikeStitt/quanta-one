"""Integration test: pose trajectory from the real wpilog file."""
from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import pytest

from quanta_io.log_source import read_wpilog_signals
from quanta_analysis.pose_trajectory import PoseTrajectoryAnalyzer
from quanta_plot.trajectory import CartesianTrajectoryPlot

REPO_ROOT = pathlib.Path(__file__).parents[3]
WPILOG = REPO_ROOT / "backgroundInfo/pyLogs/test_log_and_replay_step2.wpilog"
TEST_OUTPUT = REPO_ROOT / "test_output"
POSE_KEY = "RealOutputs/Robot/dt/Pose/estPose"


@pytest.fixture(scope="module")
def pose_result():
    if not WPILOG.exists():
        pytest.skip(f"wpilog not found: {WPILOG}")
    log_map = read_wpilog_signals(str(WPILOG))
    return PoseTrajectoryAnalyzer(POSE_KEY).process_signals(log_map)


def test_pose_trajectory_has_samples(pose_result):
    assert len(pose_result.timestamps_us) > 0, (
        f"No samples — check that '{POSE_KEY}' exists in the log"
    )


def test_pose_trajectory_has_xy_signals(pose_result):
    assert "x" in pose_result.signals
    assert "y" in pose_result.signals
    assert "vx" in pose_result.signals
    assert "vy" in pose_result.signals


def test_pose_trajectory_plot_saves_image(pose_result):
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
    fig = CartesianTrajectoryPlot().render(pose_result)
    out_path = TEST_OUTPUT / "pose_trajectory_integration.png"
    fig.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close("all")
    assert out_path.exists()
    print(f"\nPlot saved to: {out_path}")
