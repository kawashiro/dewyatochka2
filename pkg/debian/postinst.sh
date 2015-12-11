#!/bin/bash

set -u # treat unset variables as errors

id dewyatochka >/dev/null 2>&1 || useradd -Mr -s /usr/sbin/nologin -d /var/run/dewyatochka dewyatochka

for dir_ in "lib" "log"; do
    dir_abs_path="/var/${dir_}/dewyatochka"
    [[ -d "$dir_abs_path" ]] || mkdir "$dir_abs_path"
    chown -v dewyatochka:dewyatochka "$dir_abs_path"
done
