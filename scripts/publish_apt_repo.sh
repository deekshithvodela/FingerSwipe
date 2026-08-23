#!/usr/bin/env bash
set -euo pipefail

# FingerSwipe Automated APT Repository Generator
# Generates a standard Debian APT repository layout inside web/apt/

VERSION=$(grep -m1 '^version =' pyproject.toml | cut -d'"' -f2)
ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
DEB_FILE="fingerswipe_${VERSION}_${ARCH}.deb"

echo "=== FingerSwipe APT Repository Generator (v${VERSION}) ==="

# 1. Build .deb package if not present
if [ ! -f "$DEB_FILE" ]; then
    echo "[1/4] Building Debian package ${DEB_FILE}..."
    ./build_deb.sh
fi

# 2. Setup APT repository directory structure inside web/apt/
APT_DIR="web/apt"
POOL_DIR="${APT_DIR}/pool/main/f/fingerswipe"
BINARY_DIR="${APT_DIR}/dists/stable/main/binary-${ARCH}"

mkdir -p "$POOL_DIR"
mkdir -p "$BINARY_DIR"

# 3. Copy .deb package into pool
echo "[2/4] Publishing ${DEB_FILE} to pool..."
cp "$DEB_FILE" "${POOL_DIR}/"

# 4. Generate Packages and Packages.gz index files
echo "[3/4] Generating APT package indices..."
(cd "$APT_DIR" && dpkg-scanpackages pool/main /dev/null > "dists/stable/main/binary-${ARCH}/Packages")
gzip -9c "${BINARY_DIR}/Packages" > "${BINARY_DIR}/Packages.gz"

# 5. Generate Release file
echo "[4/4] Generating Release metadata..."
RELEASE_FILE="${APT_DIR}/dists/stable/Release"

cat << EOF > "$RELEASE_FILE"
Origin: FingerSwipe
Label: FingerSwipe
Suite: stable
Codename: stable
Architectures: ${ARCH}
Components: main
Description: FingerSwipe Official Debian/Ubuntu APT Repository
Date: $(date -uR)
EOF

# Calculate checksums for Packages & Packages.gz
echo "MD5Sum:" >> "$RELEASE_FILE"
(cd "${APT_DIR}/dists/stable" && md5sum main/binary-${ARCH}/Packages main/binary-${ARCH}/Packages.gz | sed 's/^/ /') >> "$RELEASE_FILE"

echo "SHA256:" >> "$RELEASE_FILE"
(cd "${APT_DIR}/dists/stable" && sha256sum main/binary-${ARCH}/Packages main/binary-${ARCH}/Packages.gz | sed 's/^/ /') >> "$RELEASE_FILE"

# 6. GPG Key Generation & Repository Release Signing
KEY_USER="FingerSwipe Automatic Signing Key <deekshithvodela@gmail.com>"
GPG_KEY_ID=$(gpg --list-secret-keys --with-colons "$KEY_USER" 2>/dev/null | grep '^sec' | cut -d: -f5 || true)

if [ -z "$GPG_KEY_ID" ]; then
    echo "[GPG] Generating FingerSwipe APT Release Signing Key..."
    gpg --batch --passphrase '' --quick-generate-key "$KEY_USER" default default 0 2>/dev/null || true
    GPG_KEY_ID=$(gpg --list-secret-keys --with-colons "$KEY_USER" 2>/dev/null | grep '^sec' | cut -d: -f5 || true)
fi

if [ -n "$GPG_KEY_ID" ]; then
    echo "[GPG] Exporting public key to web/apt/KEY.gpg..."
    gpg --armor --export "$GPG_KEY_ID" > "${APT_DIR}/KEY.gpg"

    echo "[GPG] Signing Release metadata (InRelease & Release.gpg)..."
    (cd "${APT_DIR}/dists/stable" && rm -f InRelease Release.gpg && gpg --batch --yes --default-key "$GPG_KEY_ID" -abs -o Release.gpg Release)
    (cd "${APT_DIR}/dists/stable" && gpg --batch --yes --default-key "$GPG_KEY_ID" --clearsign -o InRelease Release)
else
    echo "[WARNING] Could not obtain GPG signing key."
fi

echo "=== APT Repository Published Successfully in web/apt/ ==="
ls -lh "${BINARY_DIR}/"
ls -lh "${APT_DIR}/dists/stable/"
