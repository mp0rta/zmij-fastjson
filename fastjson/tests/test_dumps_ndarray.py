"""Tests for dumps_ndarray() - numpy ndarray JSON serialization."""

import array
import json

import pytest

np = pytest.importorskip("numpy")

import fastjson


class TestBasic1D:
    def test_float64_simple(self):
        a = np.array([1.0, 2.5, 3.0], dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[1.0,2.5,3.0]"
        assert json.loads(result) == [1.0, 2.5, 3.0]

    def test_float32_simple(self):
        a = np.array([1.0, 2.5, 3.0], dtype=np.float32)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0] == pytest.approx(1.0)
        assert parsed[1] == pytest.approx(2.5)
        assert parsed[2] == pytest.approx(3.0)

    def test_float32_shorter_than_float64_cast(self):
        """float32 via zmij_write_float should be shorter than casting to double."""
        val = np.float32(1.0 / 3.0)
        a32 = np.array([val], dtype=np.float32)
        # Cast float32 to float64 - this produces extra digits
        a64 = np.array([float(val)], dtype=np.float64)
        r32 = fastjson.dumps_ndarray(a32)
        r64 = fastjson.dumps_ndarray(a64)
        assert len(r32) <= len(r64)

    def test_empty_array(self):
        a = np.array([], dtype=np.float64)
        assert fastjson.dumps_ndarray(a) == "[]"

    def test_single_element(self):
        a = np.array([42.0], dtype=np.float64)
        assert fastjson.dumps_ndarray(a) == "[42.0]"

    def test_negative_zero(self):
        a = np.array([-0.0], dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[-0.0]"

    def test_large_array(self):
        a = np.arange(10000, dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        assert len(parsed) == 10000

    def test_roundtrip_float64(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal(1000).astype(np.float64)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        for orig, loaded in zip(a, parsed):
            assert orig == loaded

    def test_roundtrip_float32(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal(1000).astype(np.float32)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        for orig, loaded in zip(a, parsed):
            # float32 -> shortest -> parse gives back the same float32 value
            assert np.float32(loaded) == orig


class TestBasic2D:
    def test_float64_2d(self):
        a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[[1.0,2.0],[3.0,4.0]]"

    def test_float32_2d(self):
        a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        assert parsed == [[1.0, 2.0], [3.0, 4.0]]

    def test_single_row(self):
        a = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[[1.0,2.0,3.0]]"

    def test_single_column(self):
        a = np.array([[1.0], [2.0], [3.0]], dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[[1.0],[2.0],[3.0]]"

    def test_empty_rows(self):
        a = np.empty((0, 3), dtype=np.float64)
        assert fastjson.dumps_ndarray(a) == "[]"

    def test_empty_cols(self):
        a = np.empty((3, 0), dtype=np.float64)
        result = fastjson.dumps_ndarray(a)
        assert result == "[[],[],[]]"

    def test_large_2d(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal((1000, 4)).astype(np.float64)
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        assert len(parsed) == 1000
        assert all(len(row) == 4 for row in parsed)


class TestNanHandling:
    def test_nan_raise_default(self):
        a = np.array([1.0, float("nan"), 3.0], dtype=np.float64)
        with pytest.raises(ValueError, match="not JSON compliant"):
            fastjson.dumps_ndarray(a)

    def test_nan_raise_explicit(self):
        a = np.array([1.0, float("nan")], dtype=np.float64)
        with pytest.raises(ValueError):
            fastjson.dumps_ndarray(a, nan="raise")

    def test_inf_raise(self):
        a = np.array([1.0, float("inf")], dtype=np.float64)
        with pytest.raises(ValueError):
            fastjson.dumps_ndarray(a)

    def test_neg_inf_raise(self):
        a = np.array([1.0, float("-inf")], dtype=np.float64)
        with pytest.raises(ValueError):
            fastjson.dumps_ndarray(a)

    def test_nan_null_1d(self):
        a = np.array([1.0, float("nan"), 3.0], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, nan="null")
        assert result == "[1.0,null,3.0]"

    def test_inf_null_1d(self):
        a = np.array([1.0, float("inf"), float("-inf")], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, nan="null")
        assert result == "[1.0,null,null]"

    def test_nan_skip_1d(self):
        a = np.array([1.0, float("nan"), 3.0], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, nan="skip")
        assert result == "[1.0,3.0]"

    def test_nan_skip_all_nan_1d(self):
        a = np.array([float("nan"), float("inf")], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, nan="skip")
        assert result == "[]"

    def test_nan_skip_2d_skips_entire_row(self):
        a = np.array(
            [[1.0, 2.0], [3.0, float("nan")], [5.0, 6.0]], dtype=np.float64
        )
        result = fastjson.dumps_ndarray(a, nan="skip")
        assert result == "[[1.0,2.0],[5.0,6.0]]"

    def test_nan_null_2d(self):
        a = np.array([[1.0, float("nan")], [3.0, 4.0]], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, nan="null")
        assert result == "[[1.0,null],[3.0,4.0]]"

    def test_nan_float32(self):
        a = np.array([1.0, float("nan"), 3.0], dtype=np.float32)
        result = fastjson.dumps_ndarray(a, nan="null")
        parsed = json.loads(result)
        assert parsed[0] == pytest.approx(1.0)
        assert parsed[1] is None
        assert parsed[2] == pytest.approx(3.0)

    def test_nan_invalid_value(self):
        a = np.array([1.0], dtype=np.float64)
        with pytest.raises((ValueError, TypeError)):
            fastjson.dumps_ndarray(a, nan="invalid")

    def test_nan_skip_2d_all_rows_nan(self):
        a = np.array(
            [[float("nan"), 1.0], [2.0, float("inf")]], dtype=np.float64
        )
        result = fastjson.dumps_ndarray(a, nan="skip")
        assert result == "[]"


class TestPrecision:
    def test_precision_2(self):
        a = np.array([1.123456789], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, precision=2)
        assert result == "[1.12]"

    def test_precision_0(self):
        a = np.array([1.9, 2.1], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, precision=0)
        assert result == "[2,2]"

    def test_precision_6_float32(self):
        a = np.array([1.0 / 3.0], dtype=np.float32)
        result = fastjson.dumps_ndarray(a, precision=6)
        assert result == "[0.333333]"

    def test_precision_3_2d(self):
        a = np.array([[1.123456, 2.654321]], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, precision=3)
        assert result == "[[1.123,2.654]]"

    def test_precision_none_is_default(self):
        a = np.array([1.0 / 3.0], dtype=np.float64)
        r_default = fastjson.dumps_ndarray(a)
        r_none = fastjson.dumps_ndarray(a, precision=None)
        assert r_default == r_none

    def test_precision_negative_raises(self):
        a = np.array([1.0], dtype=np.float64)
        with pytest.raises(ValueError):
            fastjson.dumps_ndarray(a, precision=-1)

    def test_precision_too_large_raises(self):
        a = np.array([1.0], dtype=np.float64)
        with pytest.raises(ValueError):
            fastjson.dumps_ndarray(a, precision=21)

    def test_precision_with_nan_null(self):
        a = np.array([1.123, float("nan"), 3.456], dtype=np.float64)
        result = fastjson.dumps_ndarray(a, precision=2, nan="null")
        assert result == "[1.12,null,3.46]"


class TestEdgeCases:
    def test_fortran_order_raises(self):
        a = np.asfortranarray(np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64))
        with pytest.raises((TypeError, BufferError, ValueError)):
            fastjson.dumps_ndarray(a)

    def test_non_contiguous_slice_raises(self):
        a = np.arange(10, dtype=np.float64)[::2]
        with pytest.raises((TypeError, BufferError, ValueError)):
            fastjson.dumps_ndarray(a)

    def test_3d_raises(self):
        a = np.zeros((2, 3, 4), dtype=np.float64)
        with pytest.raises(ValueError, match="1D and 2D"):
            fastjson.dumps_ndarray(a)

    def test_int_dtype_raises(self):
        a = np.array([1, 2, 3], dtype=np.int32)
        with pytest.raises(TypeError, match="float32.*float64"):
            fastjson.dumps_ndarray(a)

    def test_non_buffer_raises(self):
        with pytest.raises((TypeError, BufferError)):
            fastjson.dumps_ndarray([1.0, 2.0, 3.0])

    def test_string_raises(self):
        with pytest.raises((TypeError, BufferError, ValueError)):
            fastjson.dumps_ndarray("hello")


class TestArrayArrayCompat:
    """array.array also supports the buffer protocol."""

    def test_array_float(self):
        a = array.array("f", [1.0, 2.5, 3.0])
        result = fastjson.dumps_ndarray(a)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0] == pytest.approx(1.0)
        assert parsed[1] == pytest.approx(2.5)

    def test_array_double(self):
        a = array.array("d", [1.0, 2.5, 3.0])
        result = fastjson.dumps_ndarray(a)
        assert result == "[1.0,2.5,3.0]"
