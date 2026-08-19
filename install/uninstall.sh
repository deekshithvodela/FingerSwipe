#!/bin/sh
set -e

# FingerSwipe Universal Linux Uninstaller

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo "${YELLOW}${BOLD}=== Uninstalling FingerSwipe ===${NC}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Administrative privileges are required. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

PREFIX="${PREFIX:-/usr/local}"
OPT_DIR="/opt/fingerswipe"

# 1. Stop and disable user services
echo "${BLUE}Stopping and disabling active user services...${NC}"
if command -v loginctl >/dev/null 2>&1; then
    for user in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
        uid=$(id -u "$user" 2>/dev/null || true)
        if [ -n "$uid" ]; then
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user stop fingerswipe.service 2>/dev/null || true
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user disable fingerswipe.service 2>/dev/null || true
        fi
    done
fi

# 2. Remove files
echo "${BLUE}Removing installed files...${NC}"
rm -rf "${OPT_DIR}"
rm -f "${PREFIX}/bin/fingerswipe"
rm -f "${PREFIX}/lib"/libfingerswipe.so*
rm -rf "${PREFIX}/include/fingerswipe"
rm -rf "${PREFIX}/share/doc/fingerswipe"
rm -f /etc/udev/rules.d/99-fingerswipe.rules /usr/lib/udev/rules.d/99-fingerswipe.rules
rm -f /etc/systemd/user/fingerswipe.service /usr/lib/systemd/user/fingerswipe.service

# 3. Reload subsystems
if command -v ldconfig >/dev/null 2>&1; then
    ldconfig
fi

if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules || true
    udevadm trigger --subsystem-match=input || true
fi

if command -v loginctl >/dev/null 2>&1; then
    for user in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
        uid=$(id -u "$user" 2>/dev/null || true)
        if [ -n "$uid" ]; then
            sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user daemon-reload 2>/dev/null || true
        fi
    done
fi

echo "${GREEN}${BOLD}✓ FingerSwipe has been uninstalled successfully.${NC}"
