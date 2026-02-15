#!/bin/bash
# Build MuttR.app using py2app
#
# Creates a standalone .app bundle with embedded Python.
# Run from the project root: ./scripts/build_app.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="MuttR"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON="${VENV_DIR}/bin/python"

echo "Building ${APP_NAME}.app with py2app..."

# Verify venv
if [ ! -f "${PYTHON}" ]; then
    echo "Error: venv not found at ${VENV_DIR}" >&2
    exit 1
fi

# Ensure py2app is installed
if ! "${PYTHON}" -c "import py2app" 2>/dev/null; then
    echo "Installing py2app..."
    "${VENV_DIR}/bin/pip" install py2app
fi

# Clean previous builds
rm -rf "${PROJECT_ROOT}/build" "${PROJECT_ROOT}/dist"

# Build
cd "${PROJECT_ROOT}"
"${PYTHON}" setup_app.py py2app

echo "Built dist/${APP_NAME}.app"

# Ad-hoc codesign with entitlements
ENTITLEMENTS="${PROJECT_ROOT}/resources/MuttR.entitlements"
echo "Signing with entitlements..."
codesign --force --deep --sign - --entitlements "${ENTITLEMENTS}" "dist/${APP_NAME}.app"

# Install to /Applications
echo "Installing to /Applications..."
if [ -d "/Applications/${APP_NAME}.app" ]; then
    rm -rf "/Applications/${APP_NAME}.app"
fi
cp -R "dist/${APP_NAME}.app" "/Applications/${APP_NAME}.app"

# Strip quarantine flag so macOS doesn't translocate the app
echo "Removing quarantine flag..."
xattr -dr com.apple.quarantine "/Applications/${APP_NAME}.app" 2>/dev/null || true

# Reset stale TCC entries so Accessibility permission matches new build
echo "Resetting Accessibility permissions (re-grant on next launch)..."
tccutil reset Accessibility com.muttr.app 2>/dev/null || true

echo "Installed to /Applications/${APP_NAME}.app"
echo ""
echo "You can now launch MuttR from:"
echo "  - Spotlight (Cmd+Space, type 'MuttR')"
echo "  - Launchpad"
echo "  - /Applications/MuttR.app"
echo ""
echo "NOTE: You will need to grant Accessibility permission on first launch."
echo "  System Settings > Privacy & Security > Accessibility > Enable MuttR"
