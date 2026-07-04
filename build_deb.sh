#!/bin/bash
set -e

echo "=== Building FingerSwipe Debian Package ==="

# 1. Compile C native library
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel

# 2. Build Python package wheel
UV_CACHE_DIR=/tmp/fingerswipe-uv-cache uv build

# 3. Clean and prepare package directory
PKG_DIR="build/package"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/lib"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/opt"

# 4. Generate Debian control file dynamically
ARCH=$(dpkg --print-architecture)
cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: fingerswipe
Version: 1.0.0
Section: sound
Priority: optional
Architecture: $ARCH
Maintainer: deevodee <deekshithvodela@gmail.com>
Depends: libinput10, libudev1, libpipewire-0.3-0, python3 (>= 3.13)
Description: Control default PipeWire sink volume with 3-finger vertical touchpad swipes.
EOF

cp debian/postinst "$PKG_DIR/DEBIAN/postinst"
cp debian/prerm "$PKG_DIR/DEBIAN/prerm"
cp debian/postrm "$PKG_DIR/DEBIAN/postrm"

# Fix permissions on control files
chmod 755 "$PKG_DIR/DEBIAN/postinst" "$PKG_DIR/DEBIAN/prerm" "$PKG_DIR/DEBIAN/postrm"

# 5. Install C library to package
cp -d build/lib/libfingerswipe.so* "$PKG_DIR/usr/lib/"

# 6. Create virtualenv and install Python wheel
uv venv --python /usr/bin/python3.13 "$PKG_DIR/opt/fingerswipe"
uv pip install --python "$PKG_DIR/opt/fingerswipe/bin/python" \
    dist/fingerswipe-1.0.0-py3-none-any.whl

# 7. Install systemd service and udev rules using installer script
"$PKG_DIR/opt/fingerswipe/bin/python" install/install.py --prefix "$PKG_DIR/usr"

# 8. Create a fully relocatable wrapper launcher script
cat << 'EOF' > "$PKG_DIR/opt/fingerswipe/bin/fingerswipe"
#!/bin/sh
exec /opt/fingerswipe/bin/python -m fingerswipe "$@"
EOF
chmod 755 "$PKG_DIR/opt/fingerswipe/bin/fingerswipe"

# 9. Create symlink in /usr/bin
ln -sf /opt/fingerswipe/bin/fingerswipe "$PKG_DIR/usr/bin/fingerswipe"

# 10. Fix internal virtualenv paths in files to avoid referencing build paths
find "$PKG_DIR/opt/fingerswipe/bin" -type f -exec grep -l "$PWD/$PKG_DIR" {} + | while read -r file; do
    sed -i "s|$PWD/$PKG_DIR||g" "$file"
done

# 11. Build the Debian package
dpkg-deb --root-owner-group --build "$PKG_DIR" fingerswipe_1.0.0_amd64.deb

echo "=== Package Built Successfully: fingerswipe_1.0.0_amd64.deb ==="
