#!/usr/bin/env bash
# Installazione utente: ./install.sh   |   Rimozione: ./install.sh --uninstall
set -e; cd "$(dirname "$0")"; P="$HOME/.local"
if [ "$1" = "--uninstall" ]; then make uninstall PREFIX="$P"; echo "LEPHOTO rimosso."; exit 0; fi
python3 -c "import gi; gi.require_version(\"Gtk\",\"4.0\"); from PIL import Image" 2>/dev/null \
  || { echo "Mancano dipendenze (python3-gi, GTK4, Pillow): vedi README.md"; exit 1; }
make install PREFIX="$P"
sed -i "s|^Exec=.*|Exec=$P/bin/lephoto %F|" "$P/share/applications/org.lephoto.App.desktop"
update-desktop-database "$P/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$P/share/icons/hicolor" 2>/dev/null || true
echo "Installato. Cerca LEPHOTO nel menu o lancia: $P/bin/lephoto"
