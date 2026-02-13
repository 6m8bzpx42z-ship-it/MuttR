#!/bin/bash
# Build MuttR.app bundle for macOS
#
# Creates a lightweight .app wrapper that launches the existing venv.
# Run from the project root: ./scripts/build_app.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="MuttR"
BUNDLE_ID="com.muttr.app"
APP_DIR="${PROJECT_ROOT}/${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
VENV_DIR="${PROJECT_ROOT}/.venv"
ICNS="${PROJECT_ROOT}/resources/MuttR.icns"

echo "Building ${APP_NAME}.app..."

# Verify prerequisites
if [ ! -d "${VENV_DIR}" ]; then
    echo "Error: venv not found at ${VENV_DIR}" >&2
    exit 1
fi

if [ ! -f "${ICNS}" ]; then
    echo "Icon not found, generating..."
    "${VENV_DIR}/bin/python" "${PROJECT_ROOT}/scripts/generate_icon.py"
fi

# Get version from setup.py
VERSION=$("${VENV_DIR}/bin/python" -c "
import re
with open('${PROJECT_ROOT}/setup.py') as f:
    m = re.search(r\"version=['\\\"]([^'\\\"]+)\", f.read())
    print(m.group(1) if m else '1.0.0')
")

# Clean previous build
rm -rf "${APP_DIR}"

# Create bundle structure
mkdir -p "${CONTENTS}/MacOS"
mkdir -p "${CONTENTS}/Resources"

# Copy icon
cp "${ICNS}" "${CONTENTS}/Resources/${APP_NAME}.icns"

# Create Info.plist
cat > "${CONTENTS}/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>MuttR needs microphone access for voice dictation.</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Create launcher script
cat > "${CONTENTS}/MacOS/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
# MuttR launcher - runs via venv python directly (no source activate needed)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENTS_DIR="$(dirname "$SCRIPT_DIR")"
APP_DIR="$(dirname "$CONTENTS_DIR")"

# Resolve the project root from where the .app lives
# If installed to /Applications, use the hardcoded project path
# If running from the project directory, use relative path
if [ -f "${APP_DIR}/../.venv/bin/python" ]; then
    PROJECT_ROOT="$(cd "${APP_DIR}/.." && pwd)"
elif [ -d "/Users/paulbrown/Desktop/coding-projects/muttr/.venv" ]; then
    PROJECT_ROOT="/Users/paulbrown/Desktop/coding-projects/muttr"
else
    osascript -e 'display dialog "MuttR Error: Could not find Python environment.\n\nPlease ensure the project venv exists." buttons {"OK"} default button "OK" with icon stop with title "MuttR"'
    exit 1
fi

VENV="${PROJECT_ROOT}/.venv"
PYTHON="${VENV}/bin/python"

# Set venv environment variables directly (avoids needing to source activate)
export VIRTUAL_ENV="${VENV}"
export PATH="${VENV}/bin:${PATH}"

# Redirect output to log file for debugging
LOG_DIR="${HOME}/Library/Logs/MuttR"
mkdir -p "${LOG_DIR}"
exec >> "${LOG_DIR}/muttr.log" 2>&1
echo "--- MuttR launch $(date) ---"
echo "Project: ${PROJECT_ROOT}"
echo "Python: ${PYTHON}"

cd "${PROJECT_ROOT}"
exec "${PYTHON}" -m muttr
LAUNCHER

chmod +x "${CONTENTS}/MacOS/${APP_NAME}"

echo "Built ${APP_DIR}"
echo "Version: ${VERSION}"

# Install to /Applications
echo "Installing to /Applications..."
if [ -d "/Applications/${APP_NAME}.app" ]; then
    rm -rf "/Applications/${APP_NAME}.app"
fi
cp -R "${APP_DIR}" "/Applications/${APP_NAME}.app"

echo "Installed to /Applications/${APP_NAME}.app"
echo ""
echo "You can now launch MuttR from:"
echo "  - Spotlight (Cmd+Space, type 'MuttR')"
echo "  - Launchpad"
echo "  - /Applications/MuttR.app"
