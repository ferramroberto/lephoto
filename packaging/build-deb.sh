#!/usr/bin/env bash
# Crea dist/lephoto_<versione>_all.deb  (richiede dpkg-deb)
set -e; cd "$(dirname "$0")/.."
V="${1:-1.0.0}"; T="$(mktemp -d)"; trap "rm -rf $T" EXIT
make install DESTDIR="$T/pkg" PREFIX=/usr
mkdir -p "$T/pkg/DEBIAN" dist
SIZE=$(du -sk "$T/pkg/usr" | cut -f1)
cat > "$T/pkg/DEBIAN/control" <<CTL
Package: lephoto
Version: $V
Section: graphics
Priority: optional
Architecture: all
Installed-Size: $SIZE
Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-4.0, python3-pil
Recommends: libjpeg-turbo-progs, gnome-screenshot | grim | spectacle | scrot, xdg-utils
Maintainer: LEPHOTO <lephoto@localhost>
Description: Viewer, editor e strumenti batch per foto
 Browser foto/video/audio, loupe, flag e stelle, rotazione lossless,
 metadati EXIF/IPTC/GPS, editor con filtri, batch, collage, GIF e altro.
CTL
for s in postinst postrm; do
cat > "$T/pkg/DEBIAN/$s" <<SH
#!/bin/sh
set -e
update-desktop-database -q /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor 2>/dev/null || true
exit 0
SH
chmod 755 "$T/pkg/DEBIAN/$s"; done
find "$T/pkg" -name __pycache__ -prune -exec rm -rf {} +
dpkg-deb --build --root-owner-group "$T/pkg" "dist/lephoto_${V}_all.deb"
echo "Creato dist/lephoto_${V}_all.deb"
