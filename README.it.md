# LEPHOTO
Viewer, editor e strumenti batch per Linux (GTK4 + Pillow).

## Struttura
    lephoto/        pacchetto Python: util, filters, editor, main_window, app
    bin/lephoto     launcher            data/   .desktop e icona SVG
    packaging/      build-deb.sh, build-rpm.sh, build-appimage.sh
    Makefile        install / uninstall / deb / rpm / appimage / all-packages

## Dipendenze runtime
- Debian/Ubuntu: `sudo apt install python3-gi gir1.2-gtk-4.0 python3-pil libjpeg-turbo-progs gnome-screenshot`
- Fedora: `sudo dnf install python3-gobject gtk4 python3-pillow libjpeg-turbo-utils gnome-screenshot`
- Arch: `sudo pacman -S python-gobject gtk4 python-pillow libjpeg-turbo gnome-screenshot`

## Installazione diretta
    ./install.sh                 # in ~/.local
    ./install.sh --uninstall
    sudo make install            # di sistema (PREFIX=/usr); DESTDIR e PREFIX supportati

## Pacchetti (generati in dist/)
    make deb         # richiede dpkg-deb               -> lephoto_1.0.0_all.deb
    make rpm         # richiede rpmbuild (rpm-build)   -> lephoto-1.0.0-1.noarch.rpm
    make appimage    # scarica appimagetool (serve rete) -> LEPHOTO-1.0.0-x86_64.AppImage
    make all-packages
La versione si cambia in `lephoto/__init__.py`.

## Note
- L'AppImage include app e Pillow, ma usa python3, PyGObject e GTK4 del sistema. Per un bundle
  totalmente autonomo servono linuxdeploy e il plugin GTK in un container (es. Ubuntu LTS) con GTK4 e PyGObject.
- Flatpak: `flatpak-builder --user --install --force-clean build-flatpak org.lephoto.App.yml`
  (senza jpegtran e senza cattura schermo, che richiederebbe il portale XDG).

## Scorciatoie (Loupe)
Frecce: naviga · F: flag · 0-5: stelle · E: editor · F11: schermo intero · Esc: esci
