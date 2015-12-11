#!/bin/bash

set -u # treat unset variables as errors

for dir_ in "lib" "log"; do
    dir_abs_path="/var/${dir_}/dewyatochka"
    if [[ -d "$dir_abs_path" ]]; then
        rmdir "/var/${dir_}/dewyatochka" --ignore-fail-on-non-empty
    fi
done
