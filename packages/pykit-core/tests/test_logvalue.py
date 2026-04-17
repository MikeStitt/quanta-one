import pytest
from pykit.logvalue import LogValue


def test_bool_inference():
    v = LogValue(True)
    assert v.log_type == LogValue.LoggableType.Boolean
    assert v.value is True


def test_int_inference():
    v = LogValue(42)
    assert v.log_type == LogValue.LoggableType.Integer


def test_float_inference():
    v = LogValue(3.14)
    assert v.log_type == LogValue.LoggableType.Double


def test_string_inference():
    v = LogValue("hello")
    assert v.log_type == LogValue.LoggableType.String


def test_bytes_inference():
    v = LogValue(b"\x01\x02")
    assert v.log_type == LogValue.LoggableType.Raw


def test_bool_list_inference():
    v = LogValue([True, False])
    assert v.log_type == LogValue.LoggableType.BooleanArray


def test_int_list_inference():
    v = LogValue([1, 2, 3])
    assert v.log_type == LogValue.LoggableType.IntegerArray


def test_float_list_inference():
    v = LogValue([1.0, 2.0])
    assert v.log_type == LogValue.LoggableType.DoubleArray


def test_string_list_inference():
    v = LogValue(["a", "b"])
    assert v.log_type == LogValue.LoggableType.StringArray


def test_bool_before_int():
    """bool is a subclass of int; must resolve to Boolean not Integer."""
    v = LogValue(True)
    assert v.log_type == LogValue.LoggableType.Boolean


def test_unsupported_type_raises():
    with pytest.raises(TypeError):
        LogValue(object())


def test_wpilog_type_roundtrip():
    for t in LogValue.LoggableType:
        type_str = t.getWPILOGType()
        recovered = LogValue.LoggableType.fromWPILOGType(type_str)
        assert recovered == t


def test_nt4_type_roundtrip():
    for t in LogValue.LoggableType:
        type_str = t.getNT4Type()
        recovered = LogValue.LoggableType.fromNT4Type(type_str)
        assert recovered == t


def test_with_type_factory():
    v = LogValue.withType(LogValue.LoggableType.Double, 1.5)
    assert v.log_type == LogValue.LoggableType.Double
    assert v.value == 1.5


def test_custom_type_overrides_wpilog_type():
    v = LogValue.withType(LogValue.LoggableType.Raw, b"", "struct:Pose2d")
    assert v.getWPILOGType() == "struct:Pose2d"


def test_unit_stored():
    v = LogValue(9.8, unit="m/s^2")
    assert v.unit == "m/s^2"
