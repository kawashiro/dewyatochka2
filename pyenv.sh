#!/usr/bin/env bash

#
# Create a new dev virtual environment
#
# usage: pyenv.sh [-i interpreter] [-p path_to_env]
#

python_path()
{
    run "$1" -c "import sys; print(sys.executable)" 2>/dev/null
}

python_dependencies()
{
    run "$1" -c "import setup; print(' '.join(setup.DEPENDS))" 2>/dev/null
}

error_exit()
{
    [[ "$1" ]] && echo "$1" 1>&2
    echo "usage: pyenv.sh [-i interpreter] [-p path_to_env]" 1>&2
    exit 1
}

run()
{
    echo "$@" 1>&2 && "$@" || exit 2
}

env_path=$(dirname "$0")/env
interpreter=$(python_path python3)
run_tests=true

while getopts ":p:i:ht" option; do
    case "${option}" in
        i)
            env_path=$(echo "$OPTARG" | sed -e "s|/+$||")
            ;;
        p)
            interpreter=$(python_path ${OPTARG}) || error_exit "Invalid interpreter path"
            ;;
        t)
            run_tests=""
            ;;
        h)
            error_exit
            ;;
        *)
            error_exit "Invalid args"
            ;;
    esac
done
shift $((OPTIND-1))

env_path_bak="$env_path"_$(date "+%Y-%m-%d_%s")

# Backup existing virtual env if needed and create a new one
[[ -d "$env_path" ]] && run mv "$env_path" "$env_path_bak"
run "$interpreter" -m venv "$env_path"

# Install dependencies into virtual env
run "${env_path}/bin/pip" install coverage $(python_dependencies "${env_path}/bin/python")

# Install config files
run mkdir "${env_path}/etc"
run cp -rv "data/etc" "${env_path}/etc/dewyatochka"

# Create app directories in filesystem
run mkdir "${env_path}/var"
for dir_ in "lib" "log" "run"; do
    run mkdir "${env_path}/var/${dir_}"
    run mkdir "${env_path}/var/${dir_}/dewyatochka"
done

# Rebuild binary extensions
extensions=$(run find "src/" -type f -name "*.so")
for extension in "$extensions"; do
    run rm -f "$extension"
done
run "${env_path}/bin/python" setup.py build_ext -i

# Run tests to ensure everything works file
if [[ "$run_tests" ]]; then
    run "${env_path}/bin/coverage" run --source=src/ test.py
    run "${env_path}/bin/coverage" html
fi
