#include <windows.h>
#include <stdio.h>
#include <R.h>
#include <Rinternals.h>

SEXP pbmc3k_terminate_process(SEXP status) {
  int code = Rf_asInteger(status);
  fflush(NULL);
  TerminateProcess(GetCurrentProcess(), (UINT) code);
  return R_NilValue;
}
