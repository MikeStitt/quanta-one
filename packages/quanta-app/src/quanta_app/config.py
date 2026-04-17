from __future__ import annotations

import tomllib
from dataclasses import dataclass, field

from quanta_analysis.analyzer import Analyzer
from quanta_plot.plot import Plot


@dataclass
class SourceConfig:
    file: str


@dataclass
class AnalysisConfig:
    type: str  # "swerve_variance" | "pose_trajectory"
    pose_key: str = ""
    odom_x_key: str = ""
    odom_y_key: str = ""
    window: int = 50


@dataclass
class OutputConfig:
    headless: bool = False
    save_path: str = "output.png"


@dataclass
class AppConfig:
    source: SourceConfig
    analysis: AnalysisConfig
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: str) -> AppConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    source = SourceConfig(file=raw["source"]["file"])

    a = raw["analysis"]
    analysis = AnalysisConfig(
        type=a["type"],
        pose_key=a.get("pose_key", ""),
        odom_x_key=a.get("odom_x_key", ""),
        odom_y_key=a.get("odom_y_key", ""),
        window=a.get("window", 50),
    )

    o = raw.get("output", {})
    output = OutputConfig(
        headless=o.get("headless", False),
        save_path=o.get("save_path", "output.png"),
    )

    return AppConfig(source=source, analysis=analysis, output=output)


def _build_analyzer(config: AppConfig) -> Analyzer:
    if config.analysis.type == "pose_trajectory":
        from quanta_analysis.pose_trajectory import PoseTrajectoryAnalyzer
        return PoseTrajectoryAnalyzer(config.analysis.pose_key)
    if config.analysis.type == "swerve_variance":
        from quanta_analysis.swerve import SwerveOdometryVarianceAnalyzer
        return SwerveOdometryVarianceAnalyzer(
            config.analysis.odom_x_key,
            config.analysis.odom_y_key,
            window=config.analysis.window,
        )
    raise ValueError(f"Unknown analysis type: {config.analysis.type!r}")


def _build_plot(config: AppConfig) -> Plot:
    if config.analysis.type == "pose_trajectory":
        from quanta_plot.trajectory import CartesianTrajectoryPlot
        return CartesianTrajectoryPlot()
    if config.analysis.type == "swerve_variance":
        from quanta_plot.variance import VarianceTimeSeriesPlot
        return VarianceTimeSeriesPlot()
    raise ValueError(f"Unknown analysis type: {config.analysis.type!r}")
