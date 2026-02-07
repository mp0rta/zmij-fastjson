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
 * bench_format_many(seq: Sequence[float]) -> int
 *
 * Batch format floats and return total string length.
 * Uses C-level loop for speed - no Python iteration overhead.
 * Raises TypeError if any element is not a float.
 */
static PyObject*
bench_format_many(PyObject* self, PyObject* args)
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
                         "bench_format_many() sequence item %zd must be float, not %.200s",
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
    {"bench_format_many", bench_format_many, METH_VARARGS,
     "bench_format_many(seq: Sequence[float]) -> int\n\n"
     "Batch format floats and return total string length.\n\n"
     "Uses C-level loop for maximum speed. All items must be floats.\n\n"
     "Args:\n"
     "    seq: Sequence of float values\n\n"
     "Returns:\n"
     "    Total length of all formatted strings"},
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
