#!/bin/bash
set -e

# Extract version and architecture
VERSION=$(grep -m1 '^version =' pyproject.toml | cut -d'"' -f2)
ARCH=$(uname -m)

echo "=== Building FingerSwipe Universal Linux Package v${VERSION} (${ARCH}) ==="

# 1. Compile C native library
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel

# 2. Build Python wheel
mkdir -p dist
UV_CACHE_DIR=/tmp/fingerswipe-uv-cache uv build

# 3. Prepare staging directory
BUNDLE_NAME="fingerswipe-${VERSION}-linux-${ARCH}"
STAGE_DIR="build/universal/${BUNDLE_NAME}"
rm -rf "build/universal"
mkdir -p "${STAGE_DIR}/lib"

# 4. Copy files
cp -d build/lib/libfingerswipe.so* "${STAGE_DIR}/lib/"
cp dist/fingerswipe-${VERSION}-*.whl "${STAGE_DIR}/"
cp install/install.sh "${STAGE_DIR}/"
cp install/uninstall.sh "${STAGE_DIR}/"
cp install/99-fingerswipe.rules "${STAGE_DIR}/"
cp install/fingerswipe.service "${STAGE_DIR}/"
cp config.yaml "${STAGE_DIR}/"
cp README.md "${STAGE_DIR}/"
cp LICENSE "${STAGE_DIR}/"

chmod +x "${STAGE_DIR}/install.sh" "${STAGE_DIR}/uninstall.sh"

# 5. Create tar.gz archive
mkdir -p dist
TAR_FILE="dist/${BUNDLE_NAME}.tar.gz"
tar --owner=0 --group=0 --numeric-owner -czf "${TAR_FILE}" -C "build/universal" "${BUNDLE_NAME}"

echo "=== Universal Linux Package Built Successfully: ${TAR_FILE} ==="
ls -lh "${TAR_FILE}"
