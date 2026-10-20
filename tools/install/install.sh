#!/bin/sh
# vn3ds for macOS: port a Ren'Py visual novel to the 3DS and put it there.
#
#   curl -fsSL https://arminjamak.github.io/vn3ds/install.sh | sh -s -- <your game>
#
# Type the command up to "--", drag the game (folder, .zip, .apk or .app) into
# the Terminal window and press Enter. Without a game it asks for one.
#
# The first time, this downloads the vn3ds-port command for your Mac (about
# 80 MB) into ~/Library/Application Support/vn3ds/cli; afterwards it is only
# downloaded again when there is a new release. Then it runs it on the game.
#
# VN3DS_DOWNLOAD_URL replaces where the download comes from (for testing).
set -eu

DOWNLOAD_URL="${VN3DS_DOWNLOAD_URL:-https://github.com/arminjamak/vn3ds/releases/latest/download}"

say() { printf '%s\n' "$*" >&2; }
die() { say "vn3ds: $*"; exit 1; }

platform() {
    [ "$(uname -s)" = "Darwin" ] || die "this installer is for macOS; on Windows use install.ps1"
    arch=$(uname -m)
    # A Terminal running under Rosetta reports x86_64 on an Apple-silicon Mac.
    if [ "$arch" = "x86_64" ] && [ "$(sysctl -n sysctl.proc_translated 2>/dev/null || echo 0)" = "1" ]; then
        arch=arm64
    fi
    case "$arch" in
        arm64) echo mac-arm64 ;;
        x86_64) echo mac-x64 ;;
        *) die "unsupported processor: $arch" ;;
    esac
}

# Something that changes when a new release is published: GitHub redirects
# .../latest/download/<asset> to the release's own URL.
release_key() {
    curl -fsSIL --max-time 20 "$1" 2>/dev/null |
        tr -d '\r' | grep -iE '^(location|content-length|etag|last-modified):' | tr '\n' ' '
}

install_cli() {
    plat=$1
    dir=$2
    asset="vn3ds-cli-$plat.tar.gz"
    url="$DOWNLOAD_URL/$asset"
    bin="$dir/vn3ds/vn3ds-port"
    key=$(release_key "$url" || true)
    if [ -x "$bin" ]; then
        if [ -z "$key" ]; then
            say "vn3ds: can't check for a newer version (offline?); using the one already here"
            return 0
        fi
        if [ -f "$dir/release" ] && [ "$(cat "$dir/release")" = "$key" ]; then
            return 0
        fi
    fi
    [ -n "$key" ] || die "can't reach $url"
    say "Downloading vn3ds ($asset)..."
    mkdir -p "$dir"
    tmp=$(mktemp -d "$dir/download.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT
    curl -fL --progress-bar -o "$tmp/$asset" "$url" || die "download failed: $url"
    if curl -fsSL --max-time 20 -o "$tmp/$asset.sha256" "$url.sha256" 2>/dev/null; then
        want=$(cut -d' ' -f1 < "$tmp/$asset.sha256")
        got=$(shasum -a 256 "$tmp/$asset" | cut -d' ' -f1)
        [ "$want" = "$got" ] || die "the download is damaged (checksum mismatch); please try again"
    fi
    mkdir "$tmp/unpacked"
    tar -xzf "$tmp/$asset" -C "$tmp/unpacked" || die "can't unpack $asset"
    [ -x "$tmp/unpacked/vn3ds/vn3ds-port" ] || die "$asset doesn't contain vn3ds/vn3ds-port"
    rm -rf "$dir/vn3ds.old"
    if [ -d "$dir/vn3ds" ]; then mv "$dir/vn3ds" "$dir/vn3ds.old"; fi
    mv "$tmp/unpacked/vn3ds" "$dir/vn3ds"
    rm -rf "$dir/vn3ds.old"
    printf '%s' "$key" > "$dir/release"
    rm -rf "$tmp"
    trap - EXIT
}

main() {
    plat=$(platform)
    dir="$HOME/Library/Application Support/vn3ds/cli"
    install_cli "$plat" "$dir"
    bin="$dir/vn3ds/vn3ds-port"
    # This script arrives through a pipe, so the program's keyboard is the
    # terminal itself (it asks for the game when none was given).
    if [ -r /dev/tty ] && { : < /dev/tty; } 2>/dev/null; then
        exec "$bin" "$@" < /dev/tty
    fi
    exec "$bin" "$@"
}

main "$@"
