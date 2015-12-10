#!/usr/bin/env bash

#
# Generate Gentoo overlay
#
# usage: genoverlay.sh destination_path
#

E_SLOT="net-misc"
E_PACKAGE="dewyatochka"
E_VERSION="9999"

error_exit()
{
    [[ "$1" ]] && echo "$1" 1>&2
    echo "usage: genoverlay.sh destination_path" 1>&2
    exit 1
}

run()
{
    echo "$@" 1>&2 && "$@" || exit 2
}

[[ $# == 1 ]] && [[ "$1" ]] || error_exit "Invalid args"
package_path="${1}/${E_SLOT}/${E_PACKAGE}"
overlay_root="${1}"
src_dir=$(dirname "$0")

# Create package directory
[[ -d "$package_path" ]] && rm -r "$package_path"
run mkdir -p "$package_path"

# Init overlay if needed
if [[ ! -f "$overlay_root/metadata/layout.conf" ]]; then
    [[ -d "$overlay_root/metadata" ]] || run mkdir "$overlay_root/metadata"
    run sh -c 'echo "masters = gentoo" > "'"$overlay_root/metadata/layout.conf"'"'
fi

# Creating package
run install -m 644 "${src_dir}/dewyatochka.ebuild" "${package_path}/${E_PACKAGE}-${E_VERSION}.ebuild"
run mkdir "${package_path}/files"
for file in "${src_dir}/files/"*; do
    if [[ -f "$file" ]]; then
        run install -m 644 "$file" "${package_path}/files/"$(basename "$file")
    fi
done
run ebuild "${package_path}/${E_PACKAGE}-${E_VERSION}.ebuild" digest
