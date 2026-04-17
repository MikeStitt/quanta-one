# Plan: Signal-Centric Data Model + Pose Trajectory + TOML Config

## Context

Three goals for this phase, layered on top of the existing monorepo:

1. **Signal-centric read path** — `quanta-io` gets a `LogSignalMap` (signal name → decoded time
   series). Analyzers can consume it via `process_signals()` instead of calling type-specific
   getters like `getDouble()` inside a per-frame loop.

2. **Pose trajectory analysis** — `PoseTrajectoryAnalyzer` reads a Pose2d signal from
   `LogSignalMap`, extracts X/Y, and computes forward velocity vectors. `CartesianTrajectoryPlot`
   renders the path with quiver arrows.

3. **TOML config + headless mode** — `quanta --config path/to/config.toml` loads a TOML config
   specifying the log file, analysis type, signal keys, and optional headless PNG output. This
   lets Claude drive test cases by writing a config file.

**Repo:** `MikeStitt/quanta-one` — commit `fe66f95` ("Add example .wpilog file.")

---

## Existing foundations (do not modify)

| File | What exists |
|---|---|
| `pykit-core/…/logtable.py` | `LogTable` — frame snapshot with typed `getDouble()` etc., `getAll() → dict[str, LogValue]` (keys include leading `/`) |
| `pykit-core/…/logvalue.py` | `LogValue` — typed union; struct values are `log_type=Raw, custom_type="struct:Foo", value=bytes` |
| `pykit-core/…/wpilog/wpilogreader.py` | `WPILOGReader` — reads PyKit-generated logs only (extra header `"PyKit"`) |
| `quanta-io/…/log_source.py` | `WPILogFileSource`, `MockLogSource` |
| `quanta-analysis/…/analyzer.py` | `Analyzer` ABC, `AnalysisResult` with `add_sample()` |
| `quanta-analysis/…/swerve.py` | `SwerveOdometryVarianceAnalyzer` (full implementation) |
| `quanta-plot/…/plot.py` | `Plot` ABC with `get_data()` |
| `quanta-plot/…/variance.py` | `VarianceTimeSeriesPlot` |
| `quanta-app/…/main.py` | `run()` + NiceGUI UI; entry point `quanta_app.main:run` |
| `backgroundInfo/pyLogs/test_log_and_replay_step2.wpilog` | Test log (PyKit-generated, present in repo) |

---

## Dependency changes

```
Before:                              After:
pykit-core                           pykit-core
    ↓                                    ↓
quanta-io                            quanta-io  ← add robotpy-wpimath>=2026.1.1
    (standalone)                         ↓       (for struct decoding)
quanta-analysis ← pykit-core        quanta-analysis ← add quanta-io dep
quanta-plot ← quanta-analysis           (LogSignalMap type crosses here)
quanta-app ← all                    quanta-plot (unchanged deps)
                                     quanta-app ← add quanta-io to main
```

`quanta-analysis` must add `quanta-io` as a dependency so that `process_signals()` can accept
`LogSignalMap` as a proper type (not `Any`). No circular deps result — the chain is linear.

---

## Python version

All five `pyproject.toml` files currently say `requires-python = ">=3.10"`. Change every one to
`">=3.13"`. No code changes needed — `tomllib` (built-in ≥3.11), `match` (3.10), `|` unions
(3.10) are already in use or available.

---

## Step 1 — Signal data model (`quanta-io`)

**New file:** `packages/quanta-io/src/quanta_io/signal.py`

```python
@dataclass
class LogSignal:
    name: str
    type_str: str           # "double", "struct:Pose2d", etc.
    timestamps_us: list[int] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)

class LogSignalMap:
    def __init__(self, signals: dict[str, LogSignal]) -> None: ...
    def __getitem__(self, name: str) -> LogSignal: ...
    def __contains__(self, name: str) -> bool: ...
    def keys(self) -> KeysView[str]: ...
    def field_names(self) -> list[str]:
        """All keys excluding those starting with '.schema/'."""
```

**Key prefix convention:** `LogSignalMap` keys strip the leading `/` that `getAll()` returns.
A key stored in `LogTable` as `"/Drive/OdometryX"` becomes `"Drive/OdometryX"` in
`LogSignalMap`. This matches the format used in analyzer constructors and TOML config files.

---

## Step 2 — Struct type registry (`quanta-io`)

**New file:** `packages/quanta-io/src/quanta_io/struct_registry.py`

```python
class StructTypeRegistry:
    def register(self, type_str: str, decoder: Callable[[bytes], Any]) -> None: ...
    def decode(self, type_str: str, raw: bytes) -> Any: ...
    def can_decode(self, type_str: str) -> bool: ...

def _build_default_registry() -> StructTypeRegistry:
    """Import wpimath (declared dep); register Pose2d, Rotation2d, Translation2d,
    Transform2d, Twist2d, ChassisSpeeds, SwerveModuleState, SwerveModulePosition
    using wpiutil.wpistruct.unpack(StructClass, bytes).
    Falls back to empty registry only if wpimath is somehow missing."""

default_registry = _build_default_registry()
```

Decoder pattern for each type:
```python
from wpimath.geometry import Pose2d
registry.register("struct:Pose2d", lambda b: wpistruct.unpack(Pose2d, b))
```

---

## Step 3 — `build_signal_map` + `read_wpilog_signals` (`quanta-io`)

**Edit:** `packages/quanta-io/src/quanta_io/log_source.py` — append two functions

```python
def build_signal_map(
    tables: Iterable[LogTable],
    registry: StructTypeRegistry | None = None,
) -> LogSignalMap:
    """Pivot Iterable[LogTable] → LogSignalMap.

    For each LogTable snapshot, calls table.getAll() → {key: LogValue}.
    - Strips the leading '/' from each key (so '/Drive/X' → 'Drive/X').
    - Skips keys starting with '.schema/' after stripping.
    - For Raw LogValue with custom_type 'struct:*': attempts registry.decode();
      stores raw bytes on miss.
    - Appends (timestamp_us, decoded_value) to each signal.
    """

def read_wpilog_signals(
    path: str,
    registry: StructTypeRegistry | None = None,
) -> LogSignalMap:
    return build_signal_map(WPILogFileSource(path), registry)
```

**Dep addition** to `packages/quanta-io/pyproject.toml`:
```toml
"robotpy-wpimath>=2026.1.1",
```

**Tests:** `packages/quanta-io/tests/test_signal.py` (new file)

| Test | Asserts |
|---|---|
| `test_empty_source_returns_empty_map` | `len(log_map.field_names()) == 0` |
| `test_double_signal_decoded` | value in `signal.values` is `float` |
| `test_timestamps_correct` | `signal.timestamps_us` matches LogTable timestamps |
| `test_schema_entries_excluded` | `"/.schema/..."` absent from `field_names()` |
| `test_unknown_struct_stored_as_bytes` | unregistered struct → raw bytes, no error |
| `test_signal_contains` | `"key" in log_map` is True |

Use `MockLogSource` for all — no file I/O. For struct test, pass `bytes` directly via
`LogValue.withType(LogValue.LoggableType.Raw, b"\x00"*48, "struct:Unknown")`.

---

## Step 4 — `process_signals` on `Analyzer` + `SwerveOdometryVarianceAnalyzer`

**Edit:** `packages/quanta-analysis/src/quanta_analysis/analyzer.py`

Add import and default implementation:
```python
from quanta_io.signal import LogSignalMap   # new dep

class Analyzer(ABC):
    # existing process() unchanged
    def process_signals(self, log_map: LogSignalMap) -> AnalysisResult:
        raise NotImplementedError(f"{type(self).__name__} does not implement process_signals()")
```

**Edit:** `packages/quanta-analysis/src/quanta_analysis/swerve.py`

Add alongside existing `process()` (keep all existing tests green):
```python
def process_signals(self, log_map: LogSignalMap) -> AnalysisResult:
    if self._odom_x_key not in log_map or self._odom_y_key not in log_map:
        return AnalysisResult()
    odom_x_sig = log_map[self._odom_x_key]
    odom_y_sig = log_map[self._odom_y_key]
    # zip timestamps from odom_x_sig; values are already decoded floats
    # reuse self._rolling_var(); build result via add_sample()
```

**Dep addition** to `packages/quanta-analysis/pyproject.toml`:
```toml
"quanta-io",
```
And add to `[tool.uv.sources]`:
```toml
quanta-io = { workspace = true }
```

---

## Step 5 — `PoseTrajectoryAnalyzer` (new, `quanta-analysis`)

**New file:** `packages/quanta-analysis/src/quanta_analysis/pose_trajectory.py`

```python
class PoseTrajectoryAnalyzer(Analyzer):
    def __init__(self, pose_key: str) -> None: ...

    def process(self, tables: Iterable[LogTable]) -> AnalysisResult:
        from quanta_io.log_source import build_signal_map
        return self.process_signals(build_signal_map(tables))

    def process_signals(self, log_map: LogSignalMap) -> AnalysisResult:
        """
        Reads log_map[self._pose_key] (struct:Pose2d values decoded by default_registry).
        Extracts x = pose.translation().X(), y = pose.translation().Y().
        vx[i] = x[i+1] - x[i], vy[i] = y[i+1] - y[i]; last point = (0.0, 0.0).
        Returns AnalysisResult with signals: x, y, vx, vy.
        """
```

**New tests:** `packages/quanta-analysis/tests/test_pose_trajectory.py`

| Test | Asserts |
|---|---|
| `test_empty_map_returns_empty_result` | no crash; `result.timestamps_us == []` |
| `test_xy_extracted_correctly` | x/y values match mock Pose2d input |
| `test_velocity_vectors_point_to_next` | `result.signals["vx"][0] == x[1] - x[0]` |
| `test_last_point_velocity_is_zero` | `result.signals["vx"][-1] == 0.0` |
| `test_timestamps_preserved` | timestamps match signal |

For tests, create mock Pose2d objects with a `.translation()` that returns an object with `.X()`
and `.Y()`, and register them in a custom `StructTypeRegistry`. Pass bytes as the raw value in
`MockLogSource` and decode via the custom registry in `build_signal_map`.

Alternatively — if it's simpler — build the `LogSignalMap` directly in the test (bypass
`build_signal_map`) by constructing `LogSignal` objects whose `.values` are already mock Pose2d
instances. This avoids struct byte-packing in unit tests entirely.

---

## Step 6 — `CartesianTrajectoryPlot` (new, `quanta-plot`)

**New file:** `packages/quanta-plot/src/quanta_plot/trajectory.py`

```python
class CartesianTrajectoryPlot(Plot):
    def render(self, result: AnalysisResult) -> plt.Figure:
        x  = result.signals.get("x", [])
        y  = result.signals.get("y", [])
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
```

**New tests:** `packages/quanta-plot/tests/test_trajectory_plot.py`

| Test | Asserts |
|---|---|
| `test_render_returns_figure` | `isinstance(fig, plt.Figure)` |
| `test_get_data_has_xy` | `"x"` and `"y"` in `get_data()` |
| `test_velocity_in_get_data` | `"vx"` and `"vy"` in `get_data()` |
| `test_empty_result_no_crash` | renders with empty `AnalysisResult`, no error |

---

## Step 7 — TOML config + headless mode (`quanta-app`)

**New file:** `packages/quanta-app/src/quanta_app/config.py`

```python
import tomllib  # built-in Python 3.11+

@dataclass
class SourceConfig:
    file: str

@dataclass
class AnalysisConfig:
    type: str           # "swerve_variance" | "pose_trajectory"
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

def load_config(path: str) -> AppConfig: ...
def _build_analyzer(config: AppConfig) -> Analyzer: ...
def _build_plot(config: AppConfig) -> Plot: ...
```

**Edit:** `packages/quanta-app/src/quanta_app/main.py` — add `main()` and `run_headless()`:

```python
def run_headless(config: AppConfig) -> None:
    log_map = read_wpilog_signals(config.source.file)
    result  = _build_analyzer(config).process_signals(log_map)
    fig     = _build_plot(config).render(result)
    pathlib.Path(config.output.save_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.output.save_path)
    plt.close("all")
    print(f"Saved: {config.output.save_path}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args, _ = parser.parse_known_args()
    if args.config:
        config = load_config(args.config)
        if config.output.headless:
            run_headless(config)
            return
    run()
```

**Edit** `packages/quanta-app/pyproject.toml` — change entry point:
```toml
quanta = "quanta_app.main:main"   # was :run
```

**New file:** `configs/pose_trajectory.toml`

```toml
[source]
file = "backgroundInfo/pyLogs/test_log_and_replay_step2.wpilog"

[analysis]
type = "pose_trajectory"
pose_key = "RealOutputs/Robot/dt/Pose/estPose"

[output]
headless = true
save_path = "output/trajectory.png"
```

---

## Critical files to touch

| File | Change |
|---|---|
| Root + all 5 `pyproject.toml` | `requires-python = ">=3.13"` |
| `quanta-io/pyproject.toml` | add `robotpy-wpimath>=2026.1.1` dep |
| `quanta-io/src/quanta_io/signal.py` | NEW |
| `quanta-io/src/quanta_io/struct_registry.py` | NEW |
| `quanta-io/src/quanta_io/log_source.py` | append `build_signal_map`, `read_wpilog_signals` |
| `quanta-io/tests/test_signal.py` | NEW (6 tests) |
| `quanta-analysis/pyproject.toml` | add `quanta-io` dep + uv source |
| `quanta-analysis/src/quanta_analysis/analyzer.py` | add `process_signals` stub |
| `quanta-analysis/src/quanta_analysis/swerve.py` | add `process_signals` impl |
| `quanta-analysis/src/quanta_analysis/pose_trajectory.py` | NEW |
| `quanta-analysis/tests/test_pose_trajectory.py` | NEW (5 tests) |
| `quanta-plot/src/quanta_plot/trajectory.py` | NEW |
| `quanta-plot/tests/test_trajectory_plot.py` | NEW (4 tests) |
| `quanta-app/src/quanta_app/config.py` | NEW |
| `quanta-app/src/quanta_app/main.py` | add `main()`, `run_headless()` |
| `quanta-app/pyproject.toml` | entry point → `:main` |
| `configs/pose_trajectory.toml` | NEW |

No changes to `pykit-core`, `variance.py`, or any existing tests.

---

## Verification

```bash
cd /path/to/quanta-one
uv python install 3.13               # one-time: get Python 3.13
uv sync --all-packages               # installs robotpy-wpimath + all workspace deps
uv run pytest packages/              # all existing + 15 new tests pass
uv run quanta --config configs/pose_trajectory.toml   # produces output/trajectory.png
uv run quanta                        # NiceGUI launches at localhost:8080
```