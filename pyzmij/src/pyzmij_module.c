#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <float.h>
#include <stdio.h>
#include <string.h>

/* Include vitaut/zmij C API header */
#include "zmij-c.h"

/*
 * pyzmij - Python binding for vitaut/zmij float formatting library
 *
 * This module provides fast float-to-string conversion using the Żmij algorithm.
 */

/*
 * Internal fast formatter using vitaut/zmij.
 */
static PyObject*
format_finite_fast(double x)
{
    char buf[zmij_double_buffer_size];
    size_t n = zmij_write_double(buf, sizeof(buf), x);
    
    if (n == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to format float");
        return NULL;
    }
    
    return PyUnicode_FromStringAndSize(buf, (Py_ssize_t)n);
}

static int
needs_dot0(const char* s, Py_ssize_t len)
{
    for (Py_ssize_t i = 0; i < len; i++) {
        char c = s[i];
        if (c == '.' || c == 'e' || c == 'E') {
            return 0;
        }
    }
    return 1;
}

static PyObject*
format_with_options(double x, int json_compatible, int allow_non_finite)
{
    if (!isfinite(x)) {
        if (!allow_non_finite) {
            PyErr_SetString(PyExc_ValueError,
                            "format() requires a finite float (not NaN or Inf)");
            return NULL;
        }
        if (isnan(x)) {
            return PyUnicode_FromString(json_compatible ? "NaN" : "nan");
        }
        if (x > 0) {
            return PyUnicode_FromString(json_compatible ? "Infinity" : "inf");
        }
        return PyUnicode_FromString(json_compatible ? "-Infinity" : "-inf");
    }

    PyObject* s = format_finite_fast(x);
    if (s == NULL) {
        return NULL;
    }
    if (!json_compatible) {
        return s;
    }

    Py_ssize_t len;
    const char* p = PyUnicode_AsUTF8AndSize(s, &len);
    if (p == NULL) {
        Py_DECREF(s);
        return NULL;
    }
    if (!needs_dot0(p, len)) {
        return s;
    }

    PyObject* out = PyUnicode_FromFormat("%U.0", s);
    Py_DECREF(s);
    return out;
}

/*
 * format_finite(x: float) -> str
 *
 * Format a finite float to its shortest decimal representation.
 * Raises TypeError if x is not a float.
 * Raises ValueError if x is NaN or Inf.
 */
static PyObject*
format_finite(PyObject* self, PyObject* args)
{
    double x;

    /* Require exact float type (no implicit conversion) */
    PyObject* obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    if (!PyFloat_Check(obj)) {
        PyErr_Format(PyExc_TypeError,
                     "format_finite() argument must be a float, not %.200s",
                     Py_TYPE(obj)->tp_name);
        return NULL;
    }

    x = PyFloat_AS_DOUBLE(obj);

    /* Check for NaN/Inf - we only handle finite values */
    if (!isfinite(x)) {
        PyErr_SetString(PyExc_ValueError,
                        "format_finite() requires a finite float (not NaN or Inf)");
        return NULL;
    }

    /* Use vitaut/zmij for fast formatting */
    return format_finite_fast(x);
}

/*
 * format(x: float, *, json_compatible: bool = False, allow_non_finite: bool = False) -> str
 */
static PyObject*
format_value(PyObject* self, PyObject* args, PyObject* kwargs)
{
    (void)self;
    PyObject* obj;
    int json_compatible = 0;
    int allow_non_finite = 0;
    static char* kwlist[] = {"x", "json_compatible", "allow_non_finite", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|pp:format", kwlist,
                                     &obj, &json_compatible, &allow_non_finite)) {
        return NULL;
    }

    if (!PyFloat_Check(obj)) {
        PyErr_Format(PyExc_TypeError,
                     "format() argument must be a float, not %.200s",
                     Py_TYPE(obj)->tp_name);
        return NULL;
    }

    return format_with_options(PyFloat_AS_DOUBLE(obj), json_compatible, allow_non_finite);
}

/*
 * format_many_len(seq: Sequence[float]) -> int
 *
 * Batch format floats and return total string length.
 * Uses C-level loop for speed - no Python iteration overhead.
 * Raises TypeError if any element is not a float.
 */
static PyObject*
format_many_len(PyObject* self, PyObject* args)
{
    PyObject* seq;

    if (!PyArg_ParseTuple(args, "O", &seq)) {
        return NULL;
    }

    /* Convert to fast sequence (list or tuple) */
    PyObject* fast = PySequence_Fast(seq, "argument must be a sequence");
    if (fast == NULL) {
        return NULL;
    }

    Py_ssize_t n = PySequence_Fast_GET_SIZE(fast);
    PyObject** items = PySequence_Fast_ITEMS(fast);

    Py_ssize_t total_len = 0;
    char buf[zmij_double_buffer_size];

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject* item = items[i];

        if (!PyFloat_Check(item)) {
            PyErr_Format(PyExc_TypeError,
                         "format_many_len() sequence item %zd must be float, not %.200s",
                         i, Py_TYPE(item)->tp_name);
            Py_DECREF(fast);
            return NULL;
        }

        double x = PyFloat_AS_DOUBLE(item);

        /* Format using vitaut/zmij */
        size_t len = zmij_write_double(buf, sizeof(buf), x);
        if (len == 0) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to format float in batch");
            Py_DECREF(fast);
            return NULL;
        }

        total_len += (Py_ssize_t)len;
    }

    Py_DECREF(fast);
    return PyLong_FromSsize_t(total_len);
}

/*
 * format_many(seq: Sequence[float], *, json_compatible: bool = False, allow_non_finite: bool = False) -> list[str]
 */
static PyObject*
format_many(PyObject* self, PyObject* args, PyObject* kwargs)
{
    (void)self;
    PyObject* seq;
    int json_compatible = 0;
    int allow_non_finite = 0;
    static char* kwlist[] = {"seq", "json_compatible", "allow_non_finite", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|pp:format_many", kwlist,
                                     &seq, &json_compatible, &allow_non_finite)) {
        return NULL;
    }

    PyObject* fast = PySequence_Fast(seq, "argument must be a sequence");
    if (fast == NULL) {
        return NULL;
    }

    Py_ssize_t n = PySequence_Fast_GET_SIZE(fast);
    PyObject** items = PySequence_Fast_ITEMS(fast);
    PyObject* out = PyList_New(n);
    if (out == NULL) {
        Py_DECREF(fast);
        return NULL;
    }

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject* item = items[i];

        if (!PyFloat_Check(item)) {
            PyErr_Format(PyExc_TypeError,
                         "format_many() sequence item %zd must be float, not %.200s",
                         i, Py_TYPE(item)->tp_name);
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }

        PyObject* s = format_with_options(PyFloat_AS_DOUBLE(item), json_compatible, allow_non_finite);
        if (s == NULL) {
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }
        PyList_SET_ITEM(out, i, s);
    }

    Py_DECREF(fast);
    return out;
}

static PyObject*
format_many_list(PyObject* seq, int json_compatible, int allow_non_finite, const char* fn_name)
{
    PyObject* fast = PySequence_Fast(seq, "argument must be a sequence");
    if (fast == NULL) {
        return NULL;
    }

    Py_ssize_t n = PySequence_Fast_GET_SIZE(fast);
    PyObject** items = PySequence_Fast_ITEMS(fast);
    PyObject* out = PyList_New(n);
    if (out == NULL) {
        Py_DECREF(fast);
        return NULL;
    }

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject* item = items[i];
        if (!PyFloat_Check(item)) {
            PyErr_Format(PyExc_TypeError,
                         "%s() sequence item %zd must be float, not %.200s",
                         fn_name, i, Py_TYPE(item)->tp_name);
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }

        PyObject* s = format_with_options(PyFloat_AS_DOUBLE(item), json_compatible, allow_non_finite);
        if (s == NULL) {
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }
        PyList_SET_ITEM(out, i, s);
    }

    Py_DECREF(fast);
    return out;
}

/*
 * format_join(seq: Sequence[float], *, sep: str = ",", json_compatible: bool = False, allow_non_finite: bool = False) -> str
 */
static PyObject*
format_join(PyObject* self, PyObject* args, PyObject* kwargs)
{
    (void)self;
    PyObject* seq;
    PyObject* sep = NULL;
    int json_compatible = 0;
    int allow_non_finite = 0;
    static char* kwlist[] = {"seq", "sep", "json_compatible", "allow_non_finite", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|Opp:format_join", kwlist,
                                     &seq, &sep, &json_compatible, &allow_non_finite)) {
        return NULL;
    }

    if (sep == NULL) {
        sep = PyUnicode_FromString(",");
        if (sep == NULL) {
            return NULL;
        }
    } else {
        Py_INCREF(sep);
    }

    if (!PyUnicode_Check(sep)) {
        Py_DECREF(sep);
        PyErr_SetString(PyExc_TypeError, "format_join() 'sep' must be str");
        return NULL;
    }

    PyObject* list = format_many_list(seq, json_compatible, allow_non_finite, "format_join");
    if (list == NULL) {
        Py_DECREF(sep);
        return NULL;
    }

    PyObject* joined = PyUnicode_Join(sep, list);
    Py_DECREF(list);
    Py_DECREF(sep);
    return joined;
}

/*
 * write_many(file, seq: Sequence[float], *, sep: str = ",", end: str = "\n", json_compatible: bool = False, allow_non_finite: bool = False)
 */
static PyObject*
write_many(PyObject* self, PyObject* args, PyObject* kwargs)
{
    (void)self;
    PyObject* file;
    PyObject* seq;
    PyObject* sep = NULL;
    PyObject* end = NULL;
    int json_compatible = 0;
    int allow_non_finite = 0;
    static char* kwlist[] = {"file", "seq", "sep", "end", "json_compatible", "allow_non_finite", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|OOpp:write_many", kwlist,
                                     &file, &seq, &sep, &end, &json_compatible, &allow_non_finite)) {
        return NULL;
    }

    if (sep == NULL) {
        sep = PyUnicode_FromString(",");
        if (sep == NULL) {
            return NULL;
        }
    } else {
        Py_INCREF(sep);
    }
    if (end == NULL) {
        end = PyUnicode_FromString("\n");
        if (end == NULL) {
            Py_DECREF(sep);
            return NULL;
        }
    } else {
        Py_INCREF(end);
    }

    if (!PyUnicode_Check(sep) || !PyUnicode_Check(end)) {
        Py_DECREF(sep);
        Py_DECREF(end);
        PyErr_SetString(PyExc_TypeError, "write_many() 'sep' and 'end' must be str");
        return NULL;
    }

    PyObject* list = format_many_list(seq, json_compatible, allow_non_finite, "write_many");
    if (list == NULL) {
        Py_DECREF(sep);
        Py_DECREF(end);
        return NULL;
    }

    PyObject* body = PyUnicode_Join(sep, list);
    Py_DECREF(list);
    Py_DECREF(sep);
    if (body == NULL) {
        Py_DECREF(end);
        return NULL;
    }

    PyObject* text = PyUnicode_Concat(body, end);
    Py_DECREF(body);
    Py_DECREF(end);
    if (text == NULL) {
        return NULL;
    }

    PyObject* result = PyObject_CallMethod(file, "write", "O", text);
    Py_DECREF(text);
    return result;
}

/*
 * backend() -> str
 *
 * Return the backend name being used ("vitaut/zmij").
 */
static PyObject*
backend(PyObject* self, PyObject* args)
{
    (void)self;  /* Unused */
    (void)args;  /* Unused */
    return PyUnicode_FromString("vitaut/zmij");
}

static PyMethodDef pyzmij_methods[] = {
    {"format", (PyCFunction)format_value, METH_VARARGS | METH_KEYWORDS,
     "format(x: float, *, json_compatible: bool = False, allow_non_finite: bool = False) -> str\n\n"
     "Format a float with optional JSON compatibility and non-finite handling.\n\n"
     "Args:\n"
     "    x: Float value to format\n"
     "    json_compatible: If True, use JSON-style float text rules:\n"
     "      - finite integer-looking values keep .0 (for example 1.0 -> \"1.0\")\n"
     "      - negative zero keeps its sign (for example -0.0 -> \"-0.0\")\n"
     "      - with allow_non_finite=True, non-finite uses JSON tokens (NaN/Infinity/-Infinity)\n"
     "    allow_non_finite: If True, allow NaN/Inf values\n\n"
     "Returns:\n"
     "    Formatted float string"},
    {"format_finite", format_finite, METH_VARARGS,
     "format_finite(x: float) -> str\n\n"
     "Format a finite float to its shortest decimal representation.\n\n"
     "Args:\n"
     "    x: A finite float value (NaN and Inf are rejected)\n\n"
     "Returns:\n"
     "    Shortest decimal string representation\n\n"
     "Raises:\n"
     "    TypeError: If x is not a float\n"
     "    ValueError: If x is NaN or Inf"},
    {"format_many_len", format_many_len, METH_VARARGS,
     "format_many_len(seq: Sequence[float]) -> int\n\n"
     "Batch format floats and return total string length.\n\n"
     "Uses C-level loop for maximum speed. All items must be floats.\n\n"
     "Args:\n"
     "    seq: Sequence of float values\n\n"
     "Returns:\n"
     "    Total length of all formatted strings"},
    {"format_many", (PyCFunction)format_many, METH_VARARGS | METH_KEYWORDS,
     "format_many(seq: Sequence[float], *, json_compatible: bool = False, allow_non_finite: bool = False) -> list[str]\n\n"
     "Format a sequence of floats and return formatted strings.\n\n"
     "Args:\n"
     "    seq: Sequence of float values\n"
     "    json_compatible: If True, apply JSON-style float text rules to each item\n"
     "    allow_non_finite: If True, allow NaN/Inf values\n\n"
     "Returns:\n"
     "    List of formatted strings"},
    {"format_join", (PyCFunction)format_join, METH_VARARGS | METH_KEYWORDS,
     "format_join(seq: Sequence[float], *, sep: str = ',', json_compatible: bool = False, allow_non_finite: bool = False) -> str\n\n"
     "Format floats and return one joined string.\n\n"
     "Args:\n"
     "    seq: Sequence of float values\n"
     "    sep: Separator string inserted between formatted values\n"
     "    json_compatible: If True, apply JSON-style float text rules\n"
     "    allow_non_finite: If True, allow NaN/Inf values\n\n"
     "Returns:\n"
     "    Joined formatted string"},
    {"write_many", (PyCFunction)write_many, METH_VARARGS | METH_KEYWORDS,
     "write_many(file, seq: Sequence[float], *, sep: str = ',', end: str = '\\n', json_compatible: bool = False, allow_non_finite: bool = False)\n\n"
     "Format floats, join text, append end, and call file.write(...).\n\n"
     "Args:\n"
     "    file: Object with write(str) method\n"
     "    seq: Sequence of float values\n"
     "    sep: Separator string inserted between formatted values\n"
     "    end: Trailing string appended once\n"
     "    json_compatible: If True, apply JSON-style float text rules\n"
     "    allow_non_finite: If True, allow NaN/Inf values\n\n"
     "Returns:\n"
     "    Return value of file.write(...)"},
    {"bench_format_many", format_many_len, METH_VARARGS,
     "bench_format_many(seq: Sequence[float]) -> int\n\n"
     "Deprecated alias of format_many_len()."},
    {"backend", backend, METH_NOARGS,
     "backend() -> str\n\n"
     "Return the backend name being used ('portable' or 'refcpp')."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef pyzmij_module = {
    PyModuleDef_HEAD_INIT,
    "_pyzmij",
    "Pyzmij - Python binding for vitaut/zmij float formatting library",
    -1,
    pyzmij_methods
};

PyMODINIT_FUNC
PyInit__pyzmij(void)
{
    return PyModule_Create(&pyzmij_module);
}
