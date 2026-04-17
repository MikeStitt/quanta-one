from quanta_io.log_source import MockLogSource


def test_mock_source_yields_correct_count():
    frames = [
        {"timestamp_us": 1000, "values": {"x": 1.0}},
        {"timestamp_us": 2000, "values": {"x": 2.0}},
        {"timestamp_us": 3000, "values": {"x": 3.0}},
    ]
    tables = list(MockLogSource(frames))
    assert len(tables) == 3


def test_mock_source_timestamps():
    frames = [
        {"timestamp_us": 1000, "values": {}},
        {"timestamp_us": 5000, "values": {}},
    ]
    tables = list(MockLogSource(frames))
    assert tables[0].getTimestamp() == 1000
    assert tables[1].getTimestamp() == 5000


def test_mock_source_signal_values():
    frames = [
        {"timestamp_us": 1000, "values": {"speed": 1.5}},
        {"timestamp_us": 2000, "values": {"speed": 3.0}},
    ]
    tables = list(MockLogSource(frames))
    assert tables[0].getDouble("speed", 0.0) == 1.5
    assert tables[1].getDouble("speed", 0.0) == 3.0


def test_mock_source_empty():
    assert list(MockLogSource([])) == []


def test_mock_source_no_values_key():
    """Frames without a 'values' key should yield an empty-data table."""
    frames = [{"timestamp_us": 1000}]
    tables = list(MockLogSource(frames))
    assert len(tables) == 1
    assert tables[0].getTimestamp() == 1000


def test_mock_source_multiple_signals_per_frame():
    frames = [{"timestamp_us": 1000, "values": {"x": 1.0, "y": 2.0, "label": "ok"}}]
    table = list(MockLogSource(frames))[0]
    assert table.getDouble("x", 0.0) == 1.0
    assert table.getDouble("y", 0.0) == 2.0
    assert table.getString("label", "") == "ok"


def test_mock_source_is_reusable():
    """Iterating the same source twice should yield the same results."""
    source = MockLogSource([{"timestamp_us": 1000, "values": {"v": 7.0}}])
    first = [t.getDouble("v", 0.0) for t in source]
    second = [t.getDouble("v", 0.0) for t in source]
    assert first == second == [7.0]
