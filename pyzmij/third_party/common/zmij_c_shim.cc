// C-API shim for vitaut/zmij C++ implementation (zmij.cc).
//
// Python extensions in this repo include `zmij-c.h` which expects the
// `zmij_detail_write_{float,double}` symbols. On Windows/MSVC, building zmij.c
// is problematic due to modern C syntax, so we build zmij.cc and provide these
// C symbols as wrappers around `zmij::detail::write`.

#include "zmij.h"

extern "C" char* zmij_detail_write_float(float value, char* buffer) {
  return zmij::detail::write(value, buffer);
}

extern "C" char* zmij_detail_write_double(double value, char* buffer) {
  return zmij::detail::write(value, buffer);
}

