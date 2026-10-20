.RECIPEPREFIX = >
PREFIX ?= /usr
VERSION := $(shell sed -n "s/__version__ = \"\(.*\)\"/\1/p" lephoto/__init__.py)

install:
> install -d $(DESTDIR)$(PREFIX)/share/lephoto/lephoto $(DESTDIR)$(PREFIX)/bin
> install -m644 lephoto/*.py $(DESTDIR)$(PREFIX)/share/lephoto/lephoto/
> install -m755 bin/lephoto $(DESTDIR)$(PREFIX)/bin/lephoto
> install -Dm644 data/org.lephoto.App.desktop $(DESTDIR)$(PREFIX)/share/applications/org.lephoto.App.desktop
> install -Dm644 data/org.lephoto.App.svg $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/org.lephoto.App.svg

uninstall:
> rm -rf $(DESTDIR)$(PREFIX)/share/lephoto $(DESTDIR)$(PREFIX)/bin/lephoto \
>   $(DESTDIR)$(PREFIX)/share/applications/org.lephoto.App.desktop \
>   $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/org.lephoto.App.svg

deb:
> bash ./packaging/build-deb.sh $(VERSION)
rpm:
> bash ./packaging/build-rpm.sh $(VERSION)
appimage:
> bash ./packaging/build-appimage.sh $(VERSION)
all-packages: deb rpm appimage
clean:
> rm -rf dist build *.tar.gz; find . -name __pycache__ -exec rm -rf {} +

.PHONY: install uninstall deb rpm appimage all-packages clean
