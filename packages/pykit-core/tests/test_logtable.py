from pykit.logtable import LogTable
from pykit.logvalue import LogValue


def test_timestamp_get_set():
    table = LogTable(5000)
    assert table.getTimestamp() == 5000
    table.setTimestamp(6000)
    assert table.getTimestamp() == 6000


def test_put_get_double():
    table = LogTable(1000)
    table.put("voltage", 12.5)
    assert table.getDouble("voltage", 0.0) == 12.5


def test_put_get_integer():
    table = LogTable(1000)
    table.put("count", 7)
    assert table.getInteger("count", 0) == 7


def test_put_get_boolean():
    table = LogTable(1000)
    table.put("enabled", True)
    assert table.getBoolean("enabled", False) is True


def test_put_get_string():
    table = LogTable(1000)
    table.put("mode", "auto")
    assert table.getString("mode", "") == "auto"


def test_put_get_double_array():
    table = LogTable(1000)
    table.put("speeds", [1.0, 2.0, 3.0])
    assert table.getDoubleArray("speeds", []) == [1.0, 2.0, 3.0]


def test_put_get_integer_array():
    table = LogTable(1000)
    table.put("ids", [1, 2, 3])
    assert table.getIntegerArray("ids", []) == [1, 2, 3]


def test_put_get_boolean_array():
    table = LogTable(1000)
    table.put("flags", [True, False, True])
    assert table.getBooleanArray("flags", []) == [True, False, True]


def test_put_get_string_array():
    table = LogTable(1000)
    table.put("names", ["a", "b"])
    assert table.getStringArray("names", []) == ["a", "b"]


def test_put_get_raw():
    table = LogTable(1000)
    table.put("blob", b"\x01\x02\x03")
    assert table.getRaw("blob", b"") == b"\x01\x02\x03"


def test_default_on_missing_key():
    table = LogTable(1000)
    assert table.getDouble("missing", 99.0) == 99.0
    assert table.getString("missing", "default") == "default"


def test_type_change_blocked():
    table = LogTable(1000)
    table.put("val", 1.0)   # Double
    table.put("val", True)  # Boolean — rejected
    assert table.getDouble("val", 0.0) == 1.0


def test_subtable_prefix():
    table = LogTable(1000)
    sub = table.getSubTable("Drive")
    sub.put("speed", 2.5)
    assert "/Drive/speed" in table.getAll()
    assert sub.getDouble("speed", 0.0) == 2.5


def test_nested_subtable():
    table = LogTable(1000)
    sub = table.getSubTable("Drive").getSubTable("FL")
    sub.put("angle", 45.0)
    assert "/Drive/FL/angle" in table.getAll()


def test_get_all_subtable_only():
    table = LogTable(1000)
    table.put("top", 1.0)
    sub = table.getSubTable("Sub")
    sub.put("inner", 2.0)
    sub_only = sub.getAll(subtableOnly=True)
    assert "/Sub/inner" in sub_only
    assert "/top" not in sub_only


def test_clone_timestamp_independence():
    table = LogTable(1000)
    clone = LogTable.clone(table)
    clone.setTimestamp(2000)
    assert table.getTimestamp() == 1000
    assert clone.getTimestamp() == 2000


def test_clone_data_independence():
    table = LogTable(1000)
    table.put("x", 1.0)
    clone = LogTable.clone(table)
    # Writing a new key to clone should not appear in original
    clone.put("y", 2.0)
    assert "/y" not in table.getAll()
    assert clone.getDouble("y", 0.0) == 2.0


def test_put_value_directly():
    table = LogTable(1000)
    lv = LogValue.withType(LogValue.LoggableType.Double, 3.14)
    table.putValue("pi", lv)
    assert table.getDouble("pi", 0.0) == pytest.approx(3.14)


def test_get_generic():
    table = LogTable(1000)
    table.put("x", 42)
    assert table.get("x", 0) == 42


# pytest import needed for approx
import pytest
