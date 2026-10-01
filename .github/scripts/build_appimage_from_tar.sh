#!/usr/bin/env bash
set -euo pipefail

TAG="${1:?usage: build_appimage_from_tar.sh <tag>}"
VERSION="${TAG#v}"
ASSETS_DIR="release-assets"
NAME="xihub"

echo "Building AppImage from tarball with bundled dependencies..."
TAR_FILE=$(find "${ASSETS_DIR}" -name "*linux*.tar.gz" -o -name "*.tar.gz" | head -n 1)
if [ -z "$TAR_FILE" ] || [ ! -f "$TAR_FILE" ]; then
  echo "Error: No Linux tarball found in ${ASSETS_DIR} to build AppImage from!" >&2
  exit 1
fi

APPDIR="$(mktemp -d)"
trap 'rm -rf "$APPDIR"' EXIT

echo "Extracting $TAR_FILE into AppDir..."
tar -xzf "$TAR_FILE" -C "$APPDIR"

mkdir -p "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/512x512/apps"

ICON_SRC=".github/assets/xihub.png"
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$APPDIR/xihub.png"
  cp "$ICON_SRC" "$APPDIR/usr/share/icons/hicolor/512x512/apps/xihub.png"
  ln -sf "xihub.png" "$APPDIR/.DirIcon"
fi

cat > "$APPDIR/$NAME.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=XiHub
Comment=Learn, teach and connect
Exec=xihub
Icon=xihub
Terminal=false
Categories=Education;Network;
DESKTOP
cp "$APPDIR/$NAME.desktop" "$APPDIR/usr/share/applications/$NAME.desktop"

cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/lib:${LD_LIBRARY_PATH:-}"
cd "${HERE}"
exec "${HERE}/xihub" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "Bundling shared library dependencies (FFmpeg / libav)..."
python3 .github/scripts/bundle_appimage_deps.py "$APPDIR"

TOOL_DIR="/tmp/appimagetool-extracted"
if [ ! -d "$TOOL_DIR" ]; then
  echo "Downloading appimagetool..."
  curl -sSL -o /tmp/appimagetool "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x /tmp/appimagetool
  (cd /tmp && ./appimagetool --appimage-extract && mv squashfs-root "$TOOL_DIR")
fi

OUT_APPIMAGE="${ASSETS_DIR}/${NAME}-${VERSION}-linux-x86_64.AppImage"
echo "Creating $OUT_APPIMAGE..."
ARCH=x86_64 "$TOOL_DIR/AppRun" "$APPDIR" "$OUT_APPIMAGE"

echo "AppImage created successfully: $OUT_APPIMAGE"
