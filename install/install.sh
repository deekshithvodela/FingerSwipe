#!/bin/sh
set -e

# FingerSwipe Universal Linux Installer / Updater
# Compatible with Arch Linux, Fedora, RHEL, openSUSE, Debian, Ubuntu, Void, Alpine, etc.

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo "${CYAN}${BOLD}=== FingerSwipe Universal Linux Installer ===${NC}"

# Check for root / sudo
if [ "$(id -u)" -ne 0 ]; then
    echo "${YELLOW}This installer requires administrative privileges to install system libraries, udev rules, and systemd units.${NC}"
    echo "Re-running with sudo..."
    exec sudo "$0" "$@"
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PREFIX="${PREFIX:-/usr/local}"
OPT_DIR="/opt/fingerswipe"

echo "Installation Prefix: ${PREFIX}"
echo "Application Directory: ${OPT_DIR}"

# 1. Stop active running user service instances if updating
echo "${BLUE}Checking for active FingerSwipe user services...${NC}"
if command -v loginctl >/dev/null 2>&1; then
    for user in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
        uid=$(id -u "$user" 2>/dev/null || true)
        if [ -n "$uid" ]; then
            if sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user is-active --quiet fingerswipe.service 2>/dev/null; then
                echo "Stopping running service for user: ${user} (UID: ${uid})"
                sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user stop fingerswipe.service 2>/dev/null || true
            fi
        fi
    done
fi

# 2. Install native shared library
echo "${BLUE}Installing native C library (libfingerswipe.so)...${NC}"
mkdir -p "${PREFIX}/lib"
if [ -d "${SCRIPT_DIR}/lib" ]; then
    cp -d "${SCRIPT_DIR}/lib"/libfingerswipe.so* "${PREFIX}/lib/" 2>/dev/null || true
elif [ -f "${SCRIPT_DIR}/libfingerswipe.so" ]; then
    cp -d "${SCRIPT_DIR}"/libfingerswipe.so* "${PREFIX}/lib/" 2>/dev/null || true
elif [ -d "${SCRIPT_DIR}/../build/lib" ]; then
    cp -d "${SCRIPT_DIR}/../build/lib"/libfingerswipe.so* "${PREFIX}/lib/" 2>/dev/null || true
fi

# Ensure library cache updated
if command -v ldconfig >/dev/null 2>&1; then
    ldconfig
fi

# 3. Detect Python 3.13+ or suitable Python 3
echo "${BLUE}Setting up isolated Python environment...${NC}"
PYTHON_BIN=""
for candidate in python3.13 python3.14 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY_VER=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        PY_MAJOR=$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || true)
        PY_MINOR=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || true)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 13 ]; then
            PYTHON_BIN=$(command -v "$candidate")
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "${YELLOW}Warning: Python 3.13+ was not found directly in PATH. Falling back to default python3.${NC}"
    PYTHON_BIN=$(command -v python3 || true)
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "${RED}Error: Python 3 is required but could not be found.${NC}"
    exit 1
fi

echo "Using Python interpreter: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"

# Prepare /opt/fingerswipe virtual environment
mkdir -p "${OPT_DIR}"
if command -v uv >/dev/null 2>&1; then
    uv venv --python "${PYTHON_BIN}" --allow-existing "${OPT_DIR}" >/dev/null 2>&1 || true
else
    "${PYTHON_BIN}" -m venv "${OPT_DIR}" || true
fi

# Locate wheel package
WHEEL_FILE=$(find "${SCRIPT_DIR}" -name "fingerswipe-*.whl" | head -n 1)
if [ -z "$WHEEL_FILE" ] && [ -d "${SCRIPT_DIR}/../dist" ]; then
    WHEEL_FILE=$(find "${SCRIPT_DIR}/../dist" -name "fingerswipe-*.whl" | head -n 1)
fi

if [ -n "$WHEEL_FILE" ]; then
    echo "Installing Python package: $(basename "$WHEEL_FILE")"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "${OPT_DIR}/bin/python" --reinstall "${WHEEL_FILE}" >/dev/null
    else
        "${OPT_DIR}/bin/pip" install --force-reinstall "${WHEEL_FILE}" >/dev/null
    fi
else
    echo "${YELLOW}Warning: Pre-built wheel not found; installing from source tree.${NC}"
    if [ -f "${SCRIPT_DIR}/../pyproject.toml" ]; then
        "${OPT_DIR}/bin/pip" install "${SCRIPT_DIR}/.." >/dev/null
    fi
fi

# 4. Create launcher binary in $PREFIX/bin
mkdir -p "${PREFIX}/bin"
cat << 'EOF' > "${OPT_DIR}/bin/fingerswipe"
#!/bin/sh
exec /opt/fingerswipe/bin/python -m fingerswipe "$@"
EOF
chmod 755 "${OPT_DIR}/bin/fingerswipe"
ln -sf "${OPT_DIR}/bin/fingerswipe" "${PREFIX}/bin/fingerswipe"

# 5. Install udev rules and systemd service
echo "${BLUE}Configuring systemd service and udev permissions...${NC}"
UDEV_DIR="/etc/udev/rules.d"
[ -d "/usr/lib/udev/rules.d" ] && UDEV_DIR="/usr/lib/udev/rules.d"
mkdir -p "${UDEV_DIR}"
cp "${SCRIPT_DIR}/99-fingerswipe.rules" "${UDEV_DIR}/99-fingerswipe.rules" 2>/dev/null || \
  cp "${SCRIPT_DIR}/install/99-fingerswipe.rules" "${UDEV_DIR}/99-fingerswipe.rules" 2>/dev/null || true

SYSTEMD_DIR="/usr/lib/systemd/user"
[ -d "/etc/systemd/user" ] && [ ! -d "/usr/lib/systemd/user" ] && SYSTEMD_DIR="/etc/systemd/user"
mkdir -p "${SYSTEMD_DIR}"
cp "${SCRIPT_DIR}/fingerswipe.service" "${SYSTEMD_DIR}/fingerswipe.service" 2>/dev/null || \
  cp "${SCRIPT_DIR}/install/fingerswipe.service" "${SYSTEMD_DIR}/fingerswipe.service" 2>/dev/null || true

# Copy default config template to doc directory
mkdir -p "${PREFIX}/share/doc/fingerswipe"
cp "${SCRIPT_DIR}/config.yaml" "${PREFIX}/share/doc/fingerswipe/config.yaml" 2>/dev/null || \
  cp "${SCRIPT_DIR}/../config.yaml" "${PREFIX}/share/doc/fingerswipe/config.yaml" 2>/dev/null || true

# 6. Reload udev rules and systemd user daemons
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules || true
    udevadm trigger --subsystem-match=input || true
fi

# 7. Restart service for active users
if command -v loginctl >/dev/null 2>&1; then
    for user in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
        uid=$(id -u "$user" 2>/dev/null || true)
        if [ -n "$uid" ]; then
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user daemon-reload 2>/dev/null || true
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user enable fingerswipe.service 2>/dev/null || true
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user restart fingerswipe.service 2>/dev/null || true
        fi
    done
fi

echo ""
echo "${GREEN}${BOLD}✓ FingerSwipe installed and started successfully!${NC}"
echo "CLI binary: ${PREFIX}/bin/fingerswipe"
echo "To check status: systemctl --user status fingerswipe.service"
echo "To view logs: journalctl --user -u fingerswipe.service -f"
