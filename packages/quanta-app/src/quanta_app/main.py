"""quanta-one NiceGUI web app entry point."""
from __future__ import annotations

import argparse
import pathlib
import tempfile

import matplotlib.pyplot as plt
from nicegui import ui, events

from quanta_io.log_source import WPILogFileSource, read_wpilog_signals
from quanta_analysis.pose_trajectory import PoseTrajectoryAnalyzer
from quanta_plot.trajectory import CartesianTrajectoryPlot

POSE_KEY = "RealOutputs/Robot/dt/Pose/estPose"


@ui.page("/")
def index() -> None:
    async def handle_upload(e: events.UploadEventArguments) -> None:
        status_label.set_text(f"Processing {e.file.name} ...")
        chart_container.clear()

        content = await e.file.read()
        pass
        with tempfile.NamedTemporaryFile(suffix=".wpilog", delete=False) as f:
            f.write(content)
            tmp_path = pathlib.Path(f.name)

        try:
            log_map = read_wpilog_signals(str(tmp_path))
            result = PoseTrajectoryAnalyzer(POSE_KEY).process_signals(log_map)

            if not result.timestamps_us:
                status_label.set_text(
                    f"No pose data found for key '{POSE_KEY}'. "
                    f"Available keys: {', '.join(list(log_map.field_names())[:10])}"
                )
                return

            x  = result.signals.get("x", [])
            y  = result.signals.get("y", [])
            vx = result.signals.get("vx", [])
            vy = result.signals.get("vy", [])

            with chart_container:
                mp = ui.matplotlib(figsize=(8, 6))
                with mp.figure as fig:
                    ax = fig.gca()
                    if x:
                        ax.quiver(x, y, vx, vy, color="green",
                                  angles="xy", scale_units="xy", scale=1, zorder=2)
                    ax.plot(x, y, "o", markersize=3, label="path", zorder=3)
                    ax.set_xlabel("X (m)")
                    ax.set_ylabel("Y (m)")
                    ax.set_aspect("equal")
                    ax.legend()
                mp.update()

            n = len(result.timestamps_us)
            duration_s = result.timestamps_us[-1] / 1e6
            status_label.set_text(f"Loaded {e.name}: {n} samples, {duration_s:.1f}s")
        except Exception as exc:
            status_label.set_text(f"Error: {exc}")
        finally:
            plt.close("all")
            tmp_path.unlink(missing_ok=True)

    ui.label("quanta-one").classes("text-2xl font-bold mb-4")
    ui.label("FRC Robot Data Analysis").classes("text-gray-500 mb-6")

    with ui.card().classes("w-full"):
        ui.label("Upload .wpilog file").classes("text-lg font-semibold mb-2")
        ui.upload(
            label="Select .wpilog file",
            auto_upload=True,
            multiple=False,
            on_upload=handle_upload,
        ).classes("w-full")

    chart_container = ui.column().classes("w-full mt-4")
    status_label = ui.label("").classes("text-sm text-gray-500 mt-2")


def run() -> None:
    ui.run(title="quanta-one", port=8080)


def run_headless(config) -> None:
    from quanta_app.config import _build_analyzer, _build_plot
    log_map = read_wpilog_signals(config.source.file)
    result = _build_analyzer(config).process_signals(log_map)
    fig = _build_plot(config).render(result)
    pathlib.Path(config.output.save_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.output.save_path)
    plt.close("all")
    print(f"Saved: {config.output.save_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args, _ = parser.parse_known_args()
    if args.config:
        from quanta_app.config import load_config
        config = load_config(args.config)
        if config.output.headless:
            run_headless(config)
            return
    run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
