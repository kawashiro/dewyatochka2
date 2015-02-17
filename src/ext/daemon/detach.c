#include <stdio.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>

#include "detach.h"


/* Fork  and detach a main process from console */
int daemon_detach(char* error_str)
{
    char* err_msg;
    pid_t pid;

    pid = fork();
    if (pid == -1) {
        sprintf(error_str, "fork() failed: %d (%s)", errno, strerror(errno));
        return 1;
    } else if (pid > 0) {
        exit(0);
    }

    if (setsid() == -1) {
        sprintf(error_str, "setsid() failed: %d (%s)", errno, strerror(errno));
        return 1;
    }

    pid = fork();
    if (pid == -1) {
        sprintf(error_str, "fork() failed: %d (%s)", errno, strerror(errno));
        return 1;
    } else if (pid > 0) {
        exit(0);
    }

    FILE* null_out = fopen(OUT_FAKE_FILE, "rw");
    if (null_out == NULL) {
        sprintf(error_str, "fopen() failed: %d (%s)", errno, strerror(errno));
        return 1;
    }

    int null_out_d = fileno(null_out);

    fclose(stdout);
    fclose(stderr);
    dup2(null_out_d, STDOUT_FILENO);
    dup2(STDERR_FILENO, STDOUT_FILENO);

    return 0;
}
