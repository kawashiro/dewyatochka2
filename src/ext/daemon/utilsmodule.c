#include <stdio.h>
#include <errno.h>

#include <Python.h>


/* Close STDIN / STDOUT / STDERR */
static PyObject* daemon_utils_close_io(PyObject* self, PyObject* args)
{
    char *err_msg;
    char *stdout_file_name = NULL;
    FILE *stdout_file;

    if (!PyArg_ParseTuple(args, "s", &stdout_file_name)) {
        return NULL;
    }

    stdout_file = fopen(stdout_file_name, "a+");
    if (stdout_file == NULL) {
        sprintf(err_msg, "Failed to open file %s: %s", stdout_file_name, strerror(errno));
        PyErr_SetString(PyExc_RuntimeError, err_msg);
        return NULL;
    }

    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);

    dup2(fileno(stdout_file), STDOUT_FILENO);
    dup2(STDOUT_FILENO, STDERR_FILENO);

    return Py_BuildValue("s", NULL);
}

/* Just exit */
static PyObject* daemon_utils_raw_exit(PyObject* self, PyObject* args)
{
    unsigned int exit_code;

    if (!PyArg_ParseTuple(args, "I", &exit_code)) {
        return NULL;
    }

    _exit(exit_code);
}


/* Init tables */
static PyMethodDef daemon_utils_methods[] = {
    {"close_io", daemon_utils_close_io, METH_VARARGS, "Close STDIN / STDOUT / STDERR"},
    {"exit", daemon_utils_raw_exit, METH_VARARGS, "Just exit immediately"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef daemon_utils_module = {
   PyModuleDef_HEAD_INIT,
   "dewyatochka.core.daemon._utils",
   NULL,
   -1,
   daemon_utils_methods
};

PyMODINIT_FUNC PyInit__utils(void)
{
    return PyModule_Create(&daemon_utils_module);
}
