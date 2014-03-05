PKG_NAME := pythonshare
SPECFILE = $(addsuffix .spec, $(PKG_NAME))
PKG_VERSION := $(shell awk '/^Version: /{print $$2}' < $(SPECFILE))

TARBALL := $(PKG_NAME)_$(PKG_VERSION).tar.gz

$(PKG_NAME).dsc: $(TARBALL) $(PKG_NAME).dsc.in
		$(eval MD5=$(shell md5sum $(TARBALL) | sed "s/  / $(shell stat -c '%s' $(TARBALL)) /"))
			@sed  -e 's/TEMPLATE-VERSION/$(PKG_VERSION)/' \
			      -e 's/TEMPLATE-MD5SUM-SIZE-TARBALL/ $(MD5)/' \
			      < $(PKG_NAME).dsc.in > $(PKG_NAME).dsc

$(TARBALL):
		cd "$$(git rev-parse --show-toplevel)" \
			&& rm -rf dist \
			&& python setup.py sdist \
			&& mv dist/* "$(CURDIR)/$(TARBALL)"

rpm: $(PKG_NAME).dsc $(TARBALL)
		mkdir -p ~/rpmbuild/SOURCES/
		rm -f ~/rpmbuild/SOURCES/$(TARBALL)
		cp -v $(TARBALL) ~/rpmbuild/SOURCES/
		rpmbuild -ba $(SPECFILE)
		rm -f $(PKG_NAME)*$(PKG_VERSION)*rpm
		cp -v ~/rpmbuild/RPMS/*/$(PKG_NAME)*$(PKG_VERSION)*rpm .

clean:
		rm -f $(PKG_NAME)*.tar.gz

all: clean dsc
