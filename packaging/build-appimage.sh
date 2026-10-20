#!/usr/bin/env bash
# Crea dist/LEPHOTO-<versione>-<arch>.AppImage
# Include app + Pillow; usa python3, PyGObject e GTK4 del sistema (vedi README per la variante completamente portabile).
set -e; cd "$(dirname "$0")/.."
V="${1:-1.0.0}"; ARCH="${ARCH:-$(uname -m)}"; A="build/AppDir"
rm -rf build; mkdir -p dist build
make install DESTDIR="$A" PREFIX=/usr
python3 -m pip install --quiet --target "$A/usr/lib/python-deps" pillow
cp data/org.lephoto.App.desktop "$A/"; sed -i "s|^Exec=.*|Exec=lephoto %F|" "$A/org.lephoto.App.desktop"
cp data/org.lephoto.App.svg "$A/"; cp data/org.lephoto.App.svg "$A/.DirIcon"
cat > "$A/AppRun" <<"RUN"
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$HERE/usr/lib/python-deps:$HERE/usr/share/lephoto:$PYTHONPATH"
export XDG_DATA_DIRS="$HERE/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
if ! python3 -c "import gi; gi.require_version(\"Gtk\",\"4.0\")" 2>/dev/null; then
  echo "LEPHOTO richiede python3-gi e GTK4 (gir1.2-gtk-4.0 / gtk4)." >&2; exit 1; fi
exec python3 "$HERE/usr/bin/lephoto" "$@"
RUN
chmod +x "$A/AppRun"
TOOL="$(command -v appimagetool || true)"
if [ -z "$TOOL" ]; then
  TOOL="build/appimagetool"
  curl -fL -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
  chmod +x "$TOOL"
fi
ARCH="$ARCH" "$TOOL" --appimage-extract-and-run "$A" "dist/LEPHOTO-${V}-${ARCH}.AppImage" 2>&1 | tail -3 \
  || ARCH="$ARCH" "$TOOL" "$A" "dist/LEPHOTO-${V}-${ARCH}.AppImage"
ls -la dist/LEPHOTO-*.AppImage
