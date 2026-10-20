# LEPHOTO

A photo viewer, editor and batch toolkit for Linux, built with GTK4 and Pillow.
Inspired by PhotoScape X.

*Italiano: see [README.it.md](README.it.md).*

## Features

**Viewer**
- Photo / Video / Audio browser with thumbnail grid and multi-selection
- Loupe view (with 1:1 zoom) and full-screen mode
- Flag and 1-5 star rating (stored in `~/.config/lephoto/meta.json`)
- Lossless JPEG rotation (via `jpegtran`; other formats are re-encoded)
- Share: email (with attachment), Twitter/X and Facebook compose pages
- Metadata viewer: EXIF, IPTC and GPS (with an OpenStreetMap link)

**Editor**
- About 40 filters and effects with search (Sepia, HDR, Miniature, Bloom, Duotone, Light Leak, Lens Flare, Old Photo, ...)
- Brightness, contrast, saturation and sharpness adjustments
- Rotate, flip, straighten, resize, crop, circular crop
- Local adjustments: apply a filter only inside a selection (mask)
- Objects: text and frames/borders
- Magic Eraser (background removal by click)
- Color picker with magnified preview, copies the hex value to the clipboard
- Undo / Redo, Projects (`.lephoto`) and Macros

**Tools**
- Batch: edit / macro, format conversion, resize, rename
- Collage, Combine (horizontal or vertical), Split
- Animated GIF creator
- Print
- Screen capture

Batch outputs are written to a `lephoto_out` folder next to the source files.

## Keyboard shortcuts (Loupe)

| Key | Action |
|---|---|
| Left / Right | Previous / next photo |
| F | Toggle flag |
| 0-5 | Set star rating |
| E | Open in editor |
| F11 | Toggle full screen |
| Esc | Leave full screen / back to grid |

## Requirements

- Python 3.9+
- GTK4 with PyGObject
- Pillow 9+
- Optional: `jpegtran` (lossless rotation), `xdg-utils` (email attachments),
  and one of `gnome-screenshot`, `grim`, `spectacle`, `scrot` (screen capture)

| Distribution | Command |
|---|---|
| Debian / Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0 python3-pil libjpeg-turbo-progs gnome-screenshot` |
| Fedora | `sudo dnf install python3-gobject gtk4 python3-pillow libjpeg-turbo-utils gnome-screenshot` |
| Arch | `sudo pacman -S python-gobject gtk4 python-pillow libjpeg-turbo gnome-screenshot` |

## Installation

Run from source:

    python3 -m lephoto          # from the project directory

Install for the current user (into `~/.local`):

    ./install.sh
    ./install.sh --uninstall

System-wide install:

    sudo make install           # PREFIX and DESTDIR are supported
    sudo make uninstall

## Building packages

Packages are written to `dist/`. The version is set in `lephoto/__init__.py`.

    make deb          # needs dpkg-deb         -> lephoto_1.0.0_all.deb
    make rpm          # needs rpmbuild         -> lephoto-1.0.0-1.noarch.rpm
    make appimage     # needs network access   -> LEPHOTO-1.0.0-x86_64.AppImage
    make all-packages

Installing a built package:

    sudo apt install ./dist/lephoto_1.0.0_all.deb
    sudo dnf install ./dist/lephoto-1.0.0-1.noarch.rpm
    chmod +x dist/LEPHOTO-*.AppImage && ./dist/LEPHOTO-*.AppImage

### Notes

- **AppImage:** bundles the app and Pillow, but relies on the system `python3`,
  PyGObject and GTK4. A fully self-contained bundle requires `linuxdeploy` with the
  GTK plugin, built inside a container (for example an Ubuntu LTS image) that has
  GTK4 and PyGObject installed.
- **RPM:** `rpmbuild` is available in the `rpm-build` package on Fedora, or `rpm` on Debian/Ubuntu.
- **Flatpak:** a manifest is included.

      flatpak-builder --user --install --force-clean build-flatpak org.lephoto.App.yml

  Inside the sandbox, `jpegtran` and screen capture are not available
  (screen capture would need the XDG portal).

## Project layout

    lephoto/           Python package
      util.py          shared helpers, constants, dialogs
      filters.py       filters and edit operations (used by editor, batch and macros)
      editor.py        editor window
      main_window.py   browser, loupe and batch tools
      app.py           GTK application entry point
    bin/lephoto        launcher script
    data/              .desktop file and SVG icon
    packaging/         build-deb.sh, build-rpm.sh, build-appimage.sh
    Makefile           install / uninstall / deb / rpm / appimage
    org.lephoto.App.yml  Flatpak manifest

## How editing works

Every edit is stored as a small operation such as `["filter", "Sepia"]` or
`["crop", 0.1, 0.1, 0.9, 0.9]`. The editor replays them on the original image, which
is what makes Undo/Redo, Projects and Macros possible: a Macro is just a saved list of
operations that Batch Edit can replay on many photos.

To add a filter, register a function that takes and returns a Pillow image in the
`FILTERS` dictionary in `lephoto/filters.py`.

## Not implemented yet

Lasso and brush Cut Out, perspective crop, paint and retouch brushes (Liquify, Clone
Stamp, Spot Healing, Red Eye, Mixer), Photo Merge (HDR, Focus Stacking), shapes and
arrows, Text Warp, Magnifier, and the large filter/frame/sticker catalogs.

## License

Not yet specified. Choose a license before distributing the packages
(the RPM spec currently declares MIT as a placeholder).
