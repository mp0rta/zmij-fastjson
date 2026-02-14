#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <float.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include "zmij-c.h"

/* Using vitaut/zmij for fast float formatting */

/*
 * fastjson - High-performance JSON serializer
 * 
 * Fast path: list[float] or tuple[float] with direct C formatting
 * Slow path: delegate to Python json module
 */

/* Dynamic buffer for building JSON string */
typedef struct {
    char* data;
    size_t size;
    size_t capacity;
} Buffer;

static int buffer_append(Buffer* buf, const char* str, size_t len);
static int buffer_append_char(Buffer* buf, char c);

static int needs_dot0(const char* s, size_t len) {
    for (size_t i = 0; i < len; i++) {
        char c = s[i];
        if (c == '.' || c == 'e' || c == 'E') {
            return 0;
        }
    }
    return 1;
}

static int buffer_append_finite_double(Buffer* buf, double x) {
    char buf_double[zmij_double_buffer_size];
    size_t len = zmij_write_double(buf_double, sizeof(buf_double), x);
    if (buffer_append(buf, buf_double, len) < 0) {
        return -1;
    }
    if (needs_dot0(buf_double, len)) {
        if (buffer_append(buf, ".0", 2) < 0) {
            return -1;
        }
    }
    return 0;
}

static int buffer_append_finite_float(Buffer* buf, float x) {
    char buf_float[zmij_float_buffer_size];
    size_t len = zmij_write_float(buf_float, sizeof(buf_float), x);
    if (buffer_append(buf, buf_float, len) < 0) {
        return -1;
    }
    if (needs_dot0(buf_float, len)) {
        if (buffer_append(buf, ".0", 2) < 0) {
            return -1;
        }
    }
    return 0;
}

static int buffer_append_double_json(Buffer* buf, double x, int allow_nan) {
    if (!isfinite(x)) {
        if (!allow_nan) {
            PyErr_SetString(PyExc_ValueError,
                "Out of range float values are not JSON compliant");
            return -1;
        }
        if (isnan(x)) {
            return buffer_append(buf, "NaN", 3);
        }
        if (x > 0) {
            return buffer_append(buf, "Infinity", 8);
        }
        return buffer_append(buf, "-Infinity", 9);
    }

    return buffer_append_finite_double(buf, x);
}

static int buffer_init(Buffer* buf, size_t initial_capacity) {
    buf->data = (char*)malloc(initial_capacity);
    if (buf->data == NULL) return -1;
    buf->size = 0;
    buf->capacity = initial_capacity;
    return 0;
}

static void buffer_free(Buffer* buf) {
    free(buf->data);
    buf->data = NULL;
    buf->size = 0;
    buf->capacity = 0;
}

static int buffer_append(Buffer* buf, const char* str, size_t len) {
    if (buf->size + len > buf->capacity) {
        size_t new_capacity = buf->capacity * 2;
        while (new_capacity < buf->size + len) {
            new_capacity *= 2;
        }
        char* new_data = (char*)realloc(buf->data, new_capacity);
        if (new_data == NULL) return -1;
        buf->data = new_data;
        buf->capacity = new_capacity;
    }
    memcpy(buf->data + buf->size, str, len);
    buf->size += len;
    return 0;
}

static int buffer_append_char(Buffer* buf, char c) {
    return buffer_append(buf, &c, 1);
}

/*
 * Check if object is a list or tuple containing only floats
 * Returns: 1 = yes, 0 = no
 */
static int is_float_sequence(PyObject* obj) {
    if (PyList_CheckExact(obj)) {
        Py_ssize_t n = PyList_GET_SIZE(obj);
        for (Py_ssize_t i = 0; i < n; i++) {
            if (!PyFloat_CheckExact(PyList_GET_ITEM(obj, i))) {
                return 0;
            }
        }
        return 1;
    }
    else if (PyTuple_CheckExact(obj)) {
        Py_ssize_t n = PyTuple_GET_SIZE(obj);
        for (Py_ssize_t i = 0; i < n; i++) {
            if (!PyFloat_CheckExact(PyTuple_GET_ITEM(obj, i))) {
                return 0;
            }
        }
        return 1;
    }
    return 0;
}

static int separators_equal_ascii_pair(PyObject* separators, const char* item_sep, const char* key_sep) {
    if (separators == NULL || separators == Py_None) {
        return 0;
    }

    PyObject* seq = PySequence_Fast(separators, NULL);
    if (seq == NULL) {
        PyErr_Clear();
        return 0;
    }

    if (PySequence_Fast_GET_SIZE(seq) != 2) {
        Py_DECREF(seq);
        return 0;
    }

    PyObject* item = PySequence_Fast_GET_ITEM(seq, 0);
    PyObject* key = PySequence_Fast_GET_ITEM(seq, 1);
    if (!PyUnicode_Check(item) || !PyUnicode_Check(key)) {
        Py_DECREF(seq);
        return 0;
    }

    int item_ok = (PyUnicode_CompareWithASCIIString(item, item_sep) == 0);
    int key_ok = (PyUnicode_CompareWithASCIIString(key, key_sep) == 0);
    Py_DECREF(seq);

    if (item_ok && key_ok) {
        return 1;
    }
    return 0;
}

static int get_supported_float_item_separator(PyObject* separators, const char** out, Py_ssize_t* out_len) {
    /* Match stdlib json.dumps separators for arrays.
       - separators is None / not provided => ", " (stdlib default)
       - separators == (",", ":") => "," (compact)
       - separators == (", ", ": ") => ", " (stdlib default, explicit) */
    if (separators == NULL || separators == Py_None) {
        *out = ", ";
        *out_len = 2;
        return 1;
    }

    if (separators_equal_ascii_pair(separators, ",", ":")) {
        *out = ",";
        *out_len = 1;
        return 1;
    }

    if (separators_equal_ascii_pair(separators, ", ", ": ")) {
        *out = ", ";
        *out_len = 2;
        return 1;
    }

    return 0;
}

static int get_item_separator(PyObject* separators, const char** out, Py_ssize_t* out_len) {
    if (separators == NULL || separators == Py_None) {
        *out = ", ";
        *out_len = 2;
        return 0;
    }

    PyObject* seq = PySequence_Fast(separators, NULL);
    if (seq == NULL) {
        PyErr_Clear();
        return -1;
    }
    if (PySequence_Fast_GET_SIZE(seq) != 2) {
        Py_DECREF(seq);
        return -1;
    }
    PyObject* item_sep = PySequence_Fast_GET_ITEM(seq, 0);
    if (!PyUnicode_Check(item_sep)) {
        Py_DECREF(seq);
        return -1;
    }
    *out = PyUnicode_AsUTF8AndSize(item_sep, out_len);
    Py_DECREF(seq);
    if (*out == NULL) {
        PyErr_Clear();
        return -1;
    }
    return 0;
}

static PyObject*
dumps_sequence_hybrid(PyObject* obj, PyObject* ensure_ascii, int allow_nan, PyObject* separators) {
    Py_ssize_t n;
    PyObject** items;

    if (PyList_CheckExact(obj)) {
        n = PyList_GET_SIZE(obj);
        items = ((PyListObject*)obj)->ob_item;
    }
    else if (PyTuple_CheckExact(obj)) {
        n = PyTuple_GET_SIZE(obj);
        items = ((PyTupleObject*)obj)->ob_item;
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Expected list or tuple");
        return NULL;
    }

    const char* item_sep;
    Py_ssize_t item_sep_len;
    if (get_item_separator(separators, &item_sep, &item_sep_len) < 0) {
        return NULL;
    }

    PyObject* json_module = PyImport_ImportModule("json");
    if (json_module == NULL) return NULL;
    PyObject* dumps_func = PyObject_GetAttrString(json_module, "dumps");
    Py_DECREF(json_module);
    if (dumps_func == NULL) return NULL;

    PyObject* json_kwargs = PyDict_New();
    if (json_kwargs == NULL) {
        Py_DECREF(dumps_func);
        return NULL;
    }
    PyDict_SetItemString(json_kwargs, "ensure_ascii", ensure_ascii);
    PyDict_SetItemString(json_kwargs, "allow_nan", allow_nan ? Py_True : Py_False);
    if (separators != NULL && separators != Py_None) {
        PyDict_SetItemString(json_kwargs, "separators", separators);
    }

    PyObject* call_args = PyTuple_New(1);
    if (call_args == NULL) {
        Py_DECREF(dumps_func);
        Py_DECREF(json_kwargs);
        return NULL;
    }
    Py_INCREF(Py_None);
    PyTuple_SET_ITEM(call_args, 0, Py_None);

    Buffer buf;
    if (buffer_init(&buf, n * 32 + 2) < 0) {
        Py_DECREF(dumps_func);
        Py_DECREF(json_kwargs);
        Py_DECREF(call_args);
        PyErr_NoMemory();
        return NULL;
    }

    if (buffer_append_char(&buf, '[') < 0) goto error;

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject* item = items[i];

        if (PyFloat_CheckExact(item)) {
            double x = PyFloat_AS_DOUBLE(item);
            if (buffer_append_double_json(&buf, x, allow_nan) < 0) goto error;
        }
        else if (item == Py_None) {
            if (buffer_append(&buf, "null", 4) < 0) goto error;
        }
        else if (item == Py_True) {
            if (buffer_append(&buf, "true", 4) < 0) goto error;
        }
        else if (item == Py_False) {
            if (buffer_append(&buf, "false", 5) < 0) goto error;
        }
        else if (PyLong_CheckExact(item)) {
            PyObject* s = PyObject_Str(item);
            if (s == NULL) goto error;
            Py_ssize_t slen;
            const char* sp = PyUnicode_AsUTF8AndSize(s, &slen);
            if (sp == NULL) {
                Py_DECREF(s);
                goto error;
            }
            if (buffer_append(&buf, sp, (size_t)slen) < 0) {
                Py_DECREF(s);
                goto error;
            }
            Py_DECREF(s);
        }
        else {
            PyObject* prev = PyTuple_GET_ITEM(call_args, 0);
            Py_DECREF(prev);
            Py_INCREF(item);
            PyTuple_SET_ITEM(call_args, 0, item);

            PyObject* s = PyObject_Call(dumps_func, call_args, json_kwargs);
            if (s == NULL) goto error;
            Py_ssize_t slen;
            const char* sp = PyUnicode_AsUTF8AndSize(s, &slen);
            if (sp == NULL) {
                Py_DECREF(s);
                goto error;
            }
            if (buffer_append(&buf, sp, (size_t)slen) < 0) {
                Py_DECREF(s);
                goto error;
            }
            Py_DECREF(s);
        }

        if (i < n - 1) {
            if (buffer_append(&buf, item_sep, (size_t)item_sep_len) < 0) goto error;
        }
    }

    if (buffer_append_char(&buf, ']') < 0) goto error;

    PyObject* result = PyUnicode_DecodeUTF8(buf.data, buf.size, NULL);
    buffer_free(&buf);
    Py_DECREF(dumps_func);
    Py_DECREF(json_kwargs);
    Py_DECREF(call_args);
    return result;

error:
    buffer_free(&buf);
    Py_DECREF(dumps_func);
    Py_DECREF(json_kwargs);
    Py_DECREF(call_args);
    if (!PyErr_Occurred()) PyErr_NoMemory();
    return NULL;
}

/*
 * Fast path: serialize list/tuple of floats to JSON
 */
static PyObject*
dumps_float_sequence(PyObject* obj, int allow_nan, const char* item_sep, Py_ssize_t item_sep_len) {
    Py_ssize_t n;
    PyObject** items;
    
    if (PyList_CheckExact(obj)) {
        n = PyList_GET_SIZE(obj);
        items = ((PyListObject*)obj)->ob_item;
    }
    else if (PyTuple_CheckExact(obj)) {
        n = PyTuple_GET_SIZE(obj);
        items = ((PyTupleObject*)obj)->ob_item;
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Expected list or tuple");
        return NULL;
    }
    
    /* Initialize buffer with reasonable initial size (+2 for optional ".0") */
    Buffer buf;
    if (buffer_init(&buf, n * 36 + (size_t)(n > 0 ? (n - 1) * item_sep_len : 0) + 2) < 0) {
        PyErr_NoMemory();
        return NULL;
    }
    
    /* Opening bracket */
    if (buffer_append_char(&buf, '[') < 0) goto error;
    
    /* Format each float */
    for (Py_ssize_t i = 0; i < n; i++) {
        double x = PyFloat_AS_DOUBLE(items[i]);
        if (buffer_append_double_json(&buf, x, allow_nan) < 0) goto error;
        
        /* Item separator (not after last element) */
        if (i < n - 1) {
            if (buffer_append(&buf, item_sep, (size_t)item_sep_len) < 0) goto error;
        }
    }
    
    /* Closing bracket */
    if (buffer_append_char(&buf, ']') < 0) goto error;
    
    /* Convert to Python string (ASCII is safe since JSON uses only ASCII) */
    PyObject* result = PyUnicode_DecodeASCII(buf.data, buf.size, NULL);
    buffer_free(&buf);
    return result;
    
error:
    buffer_free(&buf);
    return NULL;
}

/*
 * Slow path: delegate to Python json module
 */
static PyObject*
dumps_via_json(PyObject* obj, PyObject* ensure_ascii, int allow_nan, PyObject* separators) {
    /* Import json module */
    PyObject* json_module = PyImport_ImportModule("json");
    if (json_module == NULL) {
        return NULL;
    }
    
    /* Get json.dumps function */
    PyObject* dumps_func = PyObject_GetAttrString(json_module, "dumps");
    Py_DECREF(json_module);
    
    if (dumps_func == NULL) {
        return NULL;
    }
    
    /* Build kwargs for json.dumps */
    PyObject* json_kwargs = PyDict_New();
    if (json_kwargs == NULL) {
        Py_DECREF(dumps_func);
        return NULL;
    }
    
    /* Add ensure_ascii */
    PyDict_SetItemString(json_kwargs, "ensure_ascii", ensure_ascii);
    
    /* Add allow_nan */
    PyDict_SetItemString(json_kwargs, "allow_nan", allow_nan ? Py_True : Py_False);
    
    /* Add separators if provided */
    if (separators != NULL && separators != Py_None) {
        PyDict_SetItemString(json_kwargs, "separators", separators);
    }
    
    /* Call json.dumps(obj, **kwargs) */
    PyObject* result = PyObject_Call(dumps_func, PyTuple_Pack(1, obj), json_kwargs);
    
    Py_DECREF(dumps_func);
    Py_DECREF(json_kwargs);
    
    return result;
}

static PyObject*
dumps(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* obj;
    PyObject* ensure_ascii = Py_True;
    PyObject* separators = NULL;
    int allow_nan = 1;
    
    static char* kwlist[] = {"obj", "ensure_ascii", "separators", "allow_nan", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOi", kwlist,
                                     &obj, &ensure_ascii, &separators, &allow_nan)) {
        return NULL;
    }
    
    /* Try fast path for list/tuple of floats */
    if (is_float_sequence(obj)) {
        const char* item_sep;
        Py_ssize_t item_sep_len;
        if (get_supported_float_item_separator(separators, &item_sep, &item_sep_len)) {
            PyObject* result = dumps_float_sequence(obj, allow_nan, item_sep, item_sep_len);
            if (result != NULL || PyErr_Occurred()) {
                return result;
            }
            /* If fast path failed, clear error and try slow path */
            PyErr_Clear();
        }
    }

    /* Hybrid fast path: list/tuple with mixed types (float/None/bool/int + fallback) */
    if (PyList_CheckExact(obj) || PyTuple_CheckExact(obj)) {
        PyObject* result = dumps_sequence_hybrid(obj, ensure_ascii, allow_nan, separators);
        if (result != NULL || PyErr_Occurred()) {
            return result;
        }
        PyErr_Clear();
    }
    
    /* Slow path: use Python json module */
    return dumps_via_json(obj, ensure_ascii, allow_nan, separators);
}

/* ======================================================================
 * dumps_ndarray() - Fast ndarray serialization via PEP 3118 buffer protocol
 * ====================================================================== */

typedef enum {
    NAN_RAISE = 0,
    NAN_NULL  = 1,
    NAN_SKIP  = 2,
} NanMode;

static int parse_nan_mode(PyObject* nan_arg, NanMode* out) {
    if (nan_arg == NULL || nan_arg == Py_None) {
        *out = NAN_RAISE;
        return 0;
    }
    if (!PyUnicode_Check(nan_arg)) {
        PyErr_SetString(PyExc_TypeError,
            "nan parameter must be 'raise', 'null', or 'skip'");
        return -1;
    }
    if (PyUnicode_CompareWithASCIIString(nan_arg, "raise") == 0) {
        *out = NAN_RAISE;
    } else if (PyUnicode_CompareWithASCIIString(nan_arg, "null") == 0) {
        *out = NAN_NULL;
    } else if (PyUnicode_CompareWithASCIIString(nan_arg, "skip") == 0) {
        *out = NAN_SKIP;
    } else {
        PyErr_Format(PyExc_ValueError,
            "nan parameter must be 'raise', 'null', or 'skip', got '%U'",
            nan_arg);
        return -1;
    }
    return 0;
}

typedef struct {
    NanMode nan_mode;
    int use_precision;
    int precision;
    char format;  /* 'f' = float32, 'd' = float64 */
} FormatConfig;

static int buffer_append_precision_double(Buffer* buf, double x, int precision) {
    char tmp[64];
    int len = snprintf(tmp, sizeof(tmp), "%.*f", precision, x);
    if (len < 0 || len >= (int)sizeof(tmp)) {
        PyErr_SetString(PyExc_RuntimeError, "snprintf overflow in precision formatting");
        return -1;
    }
    return buffer_append(buf, tmp, (size_t)len);
}

/*
 * Format a single element from the data pointer.
 * Returns: 1 = written, 0 = skipped (NAN_SKIP), -1 = error
 */
static int format_element(Buffer* buf, const void* ptr, const FormatConfig* cfg) {
    if (cfg->format == 'f') {
        float x;
        memcpy(&x, ptr, sizeof(float));
        if (!isfinite(x)) {
            switch (cfg->nan_mode) {
            case NAN_RAISE:
                PyErr_SetString(PyExc_ValueError,
                    "Out of range float values are not JSON compliant");
                return -1;
            case NAN_NULL:
                return buffer_append(buf, "null", 4) < 0 ? -1 : 1;
            case NAN_SKIP:
                return 0;
            }
        }
        if (cfg->use_precision)
            return buffer_append_precision_double(buf, (double)x, cfg->precision) < 0 ? -1 : 1;
        return buffer_append_finite_float(buf, x) < 0 ? -1 : 1;
    } else {
        double x;
        memcpy(&x, ptr, sizeof(double));
        if (!isfinite(x)) {
            switch (cfg->nan_mode) {
            case NAN_RAISE:
                PyErr_SetString(PyExc_ValueError,
                    "Out of range float values are not JSON compliant");
                return -1;
            case NAN_NULL:
                return buffer_append(buf, "null", 4) < 0 ? -1 : 1;
            case NAN_SKIP:
                return 0;
            }
        }
        if (cfg->use_precision)
            return buffer_append_precision_double(buf, x, cfg->precision) < 0 ? -1 : 1;
        return buffer_append_finite_double(buf, x) < 0 ? -1 : 1;
    }
}

static int is_nonfinite_element(const void* ptr, char format) {
    if (format == 'f') {
        float x;
        memcpy(&x, ptr, sizeof(float));
        return !isfinite(x);
    } else {
        double x;
        memcpy(&x, ptr, sizeof(double));
        return !isfinite(x);
    }
}

static PyObject*
serialize_1d(const char* data, Py_ssize_t n, Py_ssize_t itemsize,
             const FormatConfig* cfg)
{
    Buffer buf;
    if (buffer_init(&buf, (size_t)n * 24 + 2) < 0) {
        PyErr_NoMemory();
        return NULL;
    }

    if (buffer_append_char(&buf, '[') < 0) goto error;

    int need_comma = 0;
    for (Py_ssize_t i = 0; i < n; i++) {
        const void* ptr = data + i * itemsize;

        if (cfg->nan_mode == NAN_SKIP && is_nonfinite_element(ptr, cfg->format))
            continue;

        if (need_comma) {
            if (buffer_append_char(&buf, ',') < 0) goto error;
        }

        int rc = format_element(&buf, ptr, cfg);
        if (rc < 0) goto error;
        need_comma = 1;
    }

    if (buffer_append_char(&buf, ']') < 0) goto error;

    {
        PyObject* result = PyUnicode_DecodeASCII(buf.data, buf.size, NULL);
        buffer_free(&buf);
        return result;
    }

error:
    buffer_free(&buf);
    if (!PyErr_Occurred()) PyErr_NoMemory();
    return NULL;
}

static int row_has_nonfinite(const char* row_data, Py_ssize_t cols,
                             Py_ssize_t itemsize, char format)
{
    for (Py_ssize_t j = 0; j < cols; j++) {
        if (is_nonfinite_element(row_data + j * itemsize, format))
            return 1;
    }
    return 0;
}

static PyObject*
serialize_2d(const char* data, Py_ssize_t rows, Py_ssize_t cols,
             Py_ssize_t itemsize, const FormatConfig* cfg)
{
    Buffer buf;
    size_t est = (size_t)rows * (size_t)cols * 24 + (size_t)rows * 2 + 2;
    if (buffer_init(&buf, est) < 0) {
        PyErr_NoMemory();
        return NULL;
    }

    if (buffer_append_char(&buf, '[') < 0) goto error;

    int need_row_comma = 0;
    for (Py_ssize_t i = 0; i < rows; i++) {
        const char* row_data = data + i * cols * itemsize;

        if (cfg->nan_mode == NAN_SKIP &&
            row_has_nonfinite(row_data, cols, itemsize, cfg->format))
            continue;

        if (need_row_comma) {
            if (buffer_append_char(&buf, ',') < 0) goto error;
        }

        if (buffer_append_char(&buf, '[') < 0) goto error;

        for (Py_ssize_t j = 0; j < cols; j++) {
            if (j > 0) {
                if (buffer_append_char(&buf, ',') < 0) goto error;
            }
            const void* ptr = row_data + j * itemsize;
            int rc = format_element(&buf, ptr, cfg);
            if (rc < 0) goto error;
        }

        if (buffer_append_char(&buf, ']') < 0) goto error;
        need_row_comma = 1;
    }

    if (buffer_append_char(&buf, ']') < 0) goto error;

    {
        PyObject* result = PyUnicode_DecodeASCII(buf.data, buf.size, NULL);
        buffer_free(&buf);
        return result;
    }

error:
    buffer_free(&buf);
    if (!PyErr_Occurred()) PyErr_NoMemory();
    return NULL;
}

static PyObject*
py_dumps_ndarray(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* array_obj;
    PyObject* nan_arg = NULL;
    PyObject* precision_arg = NULL;

    static char* kwlist[] = {"array", "nan", "precision", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OO", kwlist,
                                     &array_obj, &nan_arg, &precision_arg))
        return NULL;

    NanMode nan_mode;
    if (parse_nan_mode(nan_arg, &nan_mode) < 0)
        return NULL;

    int use_precision = 0;
    int precision = 0;
    if (precision_arg != NULL && precision_arg != Py_None) {
        precision = (int)PyLong_AsLong(precision_arg);
        if (precision == -1 && PyErr_Occurred())
            return NULL;
        if (precision < 0 || precision > 20) {
            PyErr_SetString(PyExc_ValueError, "precision must be between 0 and 20");
            return NULL;
        }
        use_precision = 1;
    }

    Py_buffer view;
    if (PyObject_GetBuffer(array_obj, &view, PyBUF_C_CONTIGUOUS | PyBUF_FORMAT) < 0)
        return NULL;

    if (view.ndim != 1 && view.ndim != 2) {
        PyBuffer_Release(&view);
        PyErr_Format(PyExc_ValueError,
            "only 1D and 2D arrays are supported, got %dD", view.ndim);
        return NULL;
    }

    char format;
    Py_ssize_t itemsize;
    if (view.format != NULL && view.format[0] == 'f' && view.format[1] == '\0') {
        format = 'f';
        itemsize = 4;
    } else if (view.format != NULL && view.format[0] == 'd' && view.format[1] == '\0') {
        format = 'd';
        itemsize = 8;
    } else {
        PyBuffer_Release(&view);
        PyErr_Format(PyExc_TypeError,
            "only float32 ('f') and float64 ('d') dtypes are supported, got '%s'",
            view.format ? view.format : "(null)");
        return NULL;
    }

    if (view.itemsize != itemsize) {
        PyBuffer_Release(&view);
        PyErr_SetString(PyExc_RuntimeError, "itemsize mismatch");
        return NULL;
    }

    FormatConfig cfg;
    cfg.nan_mode = nan_mode;
    cfg.use_precision = use_precision;
    cfg.precision = precision;
    cfg.format = format;

    PyObject* result;
    if (view.ndim == 1) {
        result = serialize_1d((const char*)view.buf, view.shape[0],
                              itemsize, &cfg);
    } else {
        result = serialize_2d((const char*)view.buf, view.shape[0], view.shape[1],
                              itemsize, &cfg);
    }

    PyBuffer_Release(&view);
    return result;
}

static PyMethodDef fastjson_methods[] = {
    {"dumps", (PyCFunction)dumps, METH_VARARGS | METH_KEYWORDS,
     "dumps(obj, *, ensure_ascii=True, separators=(', ', ': '), allow_nan=True) -> str\n\n"
     "Serialize Python object to JSON string.\n\n"
     "Fast path: list/tuple of floats is formatted directly in C using vitaut/zmij.\n"
     "Slow path: delegates to standard json module for other types."},
    {"dumps_ndarray", (PyCFunction)py_dumps_ndarray, METH_VARARGS | METH_KEYWORDS,
     "dumps_ndarray(array, *, nan='raise', precision=None) -> str\n\n"
     "Serialize a 1D or 2D C-contiguous float32/float64 array to a JSON string.\n\n"
     "Uses PEP 3118 buffer protocol; works with numpy.ndarray and array.array.\n\n"
     "Parameters:\n"
     "  array: object supporting the buffer protocol\n"
     "  nan: 'raise' (default), 'null', or 'skip'\n"
     "  precision: None (shortest representation) or int 0-20 (fixed decimal places)\n"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastjson_module = {
    PyModuleDef_HEAD_INIT,
    "_fastjson",
    "Fastjson - High-performance JSON serializer using vitaut/zmij",
    -1,
    fastjson_methods
};

PyMODINIT_FUNC
PyInit__fastjson(void) {
    return PyModule_Create(&fastjson_module);
}
