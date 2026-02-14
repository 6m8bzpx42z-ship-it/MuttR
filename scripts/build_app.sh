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

# Ad-hoc codesign
echo "Signing..."
codesign --force --deep --sign - "dist/${APP_NAME}.app"

# Install to /Applications
echo "Installing to /Applications..."
if [ -d "/Applications/${APP_NAME}.app" ]; then
    rm -rf "/Applications/${APP_NAME}.app"
fi
cp -R "dist/${APP_NAME}.app" "/Applications/${APP_NAME}.app"

echo "Installed to /Applications/${APP_NAME}.app"
echo ""
echo "You can now launch MuttR from:"
echo "  - Spotlight (Cmd+Space, type 'MuttR')"
echo "  - Launchpad"
echo "  - /Applications/MuttR.app"
