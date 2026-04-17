# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`quanta-one` is an FRC robot data analysis framework. It reads PyKit-generated `.wpilog` files or live NetworkTables streams and produces analytical plots — similar to AdvantageScope but focused on custom real-time analysis (e.g. swerve odometry variance, vision pose uncertainty).

## Monorepo Structure

uv workspace. All packages live under `packages/`. Run from the repo root:

```bash
uv sync                          # install all packages and deps
uv run pytest packages/          # run all tests
uv run pytest packages/<pkg>/    # run one package's tests
```

| Package | Import as | Purpose |
|---|---|---|
| `pykit-core` | `pykit` | HAL-free fork of PyKit: `LogValue`, `LogTable`, `WPILOGReader` |
| `quanta-io` | `quanta_io` | Data sources: `WPILogFileSource`, `MockLogSource` |
| `quanta-analysis` | `quanta_analysis` | `Analyzer` base + `AnalysisResult` |
| `quanta-plot` | `quanta_plot` | `Plot` base wrapping matplotlib |
| `quanta-app` | `quanta_app` | CLI entry point (`quanta plot <file>`) |

## Key Architectural Decisions

**pykit-core is a HAL-free fork of [PyKit](https://github.com/1757WestwoodRobotics/PyKit).** It keeps `LogValue`, `LogTable`, `LogReplaySource`, `LogDataReciever`, and `WPILOGReader` (all offline-safe). Everything that imports `hal`, `wpilib`, or `RobotController` was dropped. Sole dependency: `robotpy-wpiutil` (for `DataLogReader` and `wpistruct`).

**WPILOGReader only reads PyKit-generated logs** — it validates the extra header equals `"PyKit"`. Files from Java AdvantageKit will fail validation.

**LogTable key prefixing**: `LogTable` is created with prefix `"/"` by default. `table.put("x", 1.0)` stores the key as `"/x"`. `getSubTable("Drive")` creates a view with prefix `"/Drive/"`. Keys in `getAll()` always include the leading slash.

**Testing without images**: `Plot.get_data()` returns the arrays passed to matplotlib after a `render()` call. Tests assert on those dicts, never on rendered images. The `Agg` backend is set at import time in `quanta_plot/plot.py`.

**MockLogSource** (in `quanta_io.log_source`) creates in-memory `LogTable` sequences from plain dicts — no `.wpilog` files or wpiutil needed. Use it in all unit tests for analyzers and plots.

## Data Flow

```
WPILogFileSource  ──┐
                    ├──▶  Iterable[LogTable]  ──▶  Analyzer  ──▶  AnalysisResult  ──▶  Plot
MockLogSource     ──┘
```

## Adding a New Analyzer

Subclass `quanta_analysis.analyzer.Analyzer`, implement `process(tables) -> AnalysisResult`. Test with `MockLogSource` — no file I/O needed.

## Adding a New Plot

Subclass `quanta_plot.plot.Plot`, implement `render(result) -> Figure`. Populate `self._data` with the arrays passed to matplotlib. Test by asserting on `plot.get_data()`.
