PKG_NAME := fmbt
SPECFILE = $(addsuffix .spec, $(PKG_NAME))
PKG_VERSION := $(shell grep '^Version: ' $(SPECFILE)|awk '{print $$2}')

TARBALL := $(PKG_NAME)-$(PKG_VERSION).tar.gz

dsc:
	@sed  -i 's/ [a-f0-9]\+ [0-9]\+ $(TARBALL)/ $(shell md5sum $(TARBALL) | sed "s/  / $(shell stat -c '%s' $(TARBALL)) /")/' $(PKG_NAME).dsc

tarball:
	@cd .. && git archive --prefix $(PKG_NAME)-$(PKG_VERSION)/ HEAD \
		| gzip > packaging/$(TARBALL)

clean:
	@rm -f *.tar.gz

all: clean tarball
