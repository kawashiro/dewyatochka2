#include <errno.h>

#include <Python.h>

#include "detach.h"


/* Fork  and detach a main process from console */
static PyObject* py_daemon_detach(PyObject* self, PyObject* args)
{
    char* err_msg;

    if (daemon_detach(err_msg) != 0) {
        PyErr_SetString(PyExc_RuntimeError, err_msg);
        return NULL;
    }

    return Py_BuildValue("s", NULL);
}


/* Init tables */
static PyMethodDef daemon_methods[] = {
    {"detach", py_daemon_detach, METH_NOARGS, "Detach a process from a shell"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef daemon_module = {
   PyModuleDef_HEAD_INIT,
   "dewyatochka.core.daemon._daemon",
   NULL,
   -1,
   daemon_methods
};

PyMODINIT_FUNC PyInit__daemon(void)
{
    return PyModule_Create(&daemon_module);
}
