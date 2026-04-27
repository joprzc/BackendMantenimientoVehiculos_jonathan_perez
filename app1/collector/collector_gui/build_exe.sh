#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$BASE_DIR/dist"
BUILD_DIR="$BASE_DIR/build"
DOWNLOADS_DIR="$BASE_DIR/../../../static/app1/downloads"
MAC_ZIP="$DOWNLOADS_DIR/AutoControlCollector-macOS.zip"

rm -rf "$BUILD_DIR" "$DIST_DIR"
rm -f "$MAC_ZIP"
mkdir -p "$DOWNLOADS_DIR"

pyinstaller \
  --noconfirm \
  --onedir \
  --windowed \
  --add-data "$BASE_DIR/collector_config.json:." \
  "$BASE_DIR/autocontrol_collector_gui.py"

ditto -c -k --sequesterRsrc --keepParent \
  "$DIST_DIR/autocontrol_collector_gui.app" \
  "$MAC_ZIP"


