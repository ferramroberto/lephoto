#!/usr/bin/env bash
# Crea dist/lephoto-<versione>-1.noarch.rpm  (richiede rpmbuild: dnf install rpm-build / apt install rpm)
set -e; cd "$(dirname "$0")/.."; ROOT="$PWD"
V="${1:-1.0.0}"; T="$(mktemp -d)"; trap "rm -rf $T" EXIT
mkdir -p "$T"/{SOURCES,SPECS,BUILD,RPMS,SRPMS} dist
tar czf "$T/SOURCES/lephoto-$V.tar.gz" --exclude=dist --exclude=__pycache__ --exclude=.git \
    --transform "s,^\./,lephoto-$V/," -C "$ROOT" .
cat > "$T/SPECS/lephoto.spec" <<SPEC
Name:       lephoto
Version:    $V
Release:    1
Summary:    Viewer, editor e strumenti batch per foto
License:    MIT
BuildArch:  noarch
Source0:    lephoto-$V.tar.gz
Requires:   python3, python3-gobject, gtk4, python3-pillow
Recommends: libjpeg-turbo-utils

%description
Browser foto/video/audio, loupe, flag e stelle, rotazione lossless, metadati
EXIF/IPTC/GPS, editor con filtri, batch, collage, GIF e altro.

%prep
%setup -q

%install
make install DESTDIR=%{buildroot} PREFIX=/usr

%post
update-desktop-database &> /dev/null || :
gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || :

%files
/usr/bin/lephoto
/usr/share/lephoto
/usr/share/applications/org.lephoto.App.desktop
/usr/share/icons/hicolor/scalable/apps/org.lephoto.App.svg
SPEC
rpmbuild -bb --define "_topdir $T" "$T/SPECS/lephoto.spec"
cp "$T"/RPMS/noarch/*.rpm dist/ && echo "Creato in dist/:" && ls dist/*.rpm
