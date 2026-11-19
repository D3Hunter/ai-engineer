#!/bin/sh
# Install kennytm/dbgen v0.8.0 when it is not already on PATH.
# Prints the absolute path of the dbgen binary.
set -eu

VERSION=v0.8.0
ASSET="dbgen-${VERSION}-x86_64-unknown-linux-gnu.tar.xz"
URL="https://github.com/kennytm/dbgen/releases/download/${VERSION}/${ASSET}"

if command -v dbgen >/dev/null 2>&1; then
    command -v dbgen
    exit 0
fi

install_dir=${DBGEN_DIR:-./.dbgen}
mkdir -p "$install_dir"
install_dir=$(CDPATH= cd "$install_dir" && pwd)
binary="$install_dir/bin/dbgen"

if [ -x "$binary" ]; then
    printf '%s\n' "$binary"
    exit 0
fi

os=$(uname -s)
arch=$(uname -m)

run_priv() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        return 1
    fi
}

install_xz() {
    if command -v xz >/dev/null 2>&1; then
        return 0
    fi
    if command -v yum >/dev/null 2>&1; then
        run_priv yum install -y xz || return 1
    elif command -v dnf >/dev/null 2>&1; then
        run_priv dnf install -y xz || return 1
    elif command -v apt-get >/dev/null 2>&1; then
        run_priv apt-get update || return 1
        run_priv apt-get install -y xz-utils || return 1
    elif command -v apk >/dev/null 2>&1; then
        run_priv apk add xz || return 1
    else
        return 1
    fi
    command -v xz >/dev/null 2>&1
}

unpack_archive() {
    archive=$1
    dest=$2
    if tar -xJf "$archive" -C "$dest" 2>/dev/null; then
        return 0
    fi
    if install_xz && tar -xJf "$archive" -C "$dest"; then
        return 0
    fi
    python3 - "$archive" "$dest" <<'PY'
import sys, tarfile
tarfile.open(sys.argv[1]).extractall(sys.argv[2])
PY
}

install_release() {
    archive="$install_dir/$ASSET"
    if command -v wget >/dev/null 2>&1; then
        wget -O "$archive" "$URL"
    elif command -v curl >/dev/null 2>&1; then
        curl -fL -o "$archive" "$URL"
    else
        echo "wget or curl is required to download dbgen" >&2
        exit 1
    fi
    unpack_archive "$archive" "$install_dir"
    chmod +x "$binary"
    printf '%s\n' "$binary"
}

install_with_cargo() {
    if ! command -v cargo >/dev/null 2>&1; then
        echo "dbgen ${VERSION} publishes a binary only for x86_64-unknown-linux-gnu. This host is ${os} ${arch}, and cargo is not installed." >&2
        exit 1
    fi
    cargo install dbgen --version 0.8.0 --root "$install_dir"
    chmod +x "$binary"
    printf '%s\n' "$binary"
}

case "$os:$arch" in
    Linux:x86_64)
        install_release
        ;;
    *)
        install_with_cargo
        ;;
esac
