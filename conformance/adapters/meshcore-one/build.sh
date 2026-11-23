#!/bin/sh
# Build the MeshCore One adapter in the official Swift image, statically
# linked so it runs on the host without a Swift toolchain.
#
# Usage: build.sh <MeshCoreOne checkout>
set -eu
here=$(cd "$(dirname "$0")" && pwd)
mc1=$(cd "$1" && pwd)
src=MC1Services/Sources/MC1Services/MECP
mkdir -p "$here/build"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$here:/adapter" -v "$mc1:/mc1:ro" "${SWIFT_IMAGE:-swift:6.1-noble}" \
  sh -c "swiftc -O -static-stdlib -module-name MC1Adapter /mc1/$src/*.swift /adapter/main.swift \
    -o /adapter/build/mc1-adapter"
