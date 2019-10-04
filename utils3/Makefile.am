VPATH ?= .

dist_noinst_SCRIPTS = \
	setup.py

# scripts
# end of scripts

# modules
dist_noinst_SCRIPTS +=		\
        eyenfinger.py           \
	fmbt.py			\
	fmbt_config.py		\
	fmbtgti.py		\
	fmbtpng.py    	        \
	fmbtwindows.py		\
	fmbtwindows_agent.py	\
	pycosh.py
# end of modules

utils_installer: $(dist_noinst_SCRIPTS)
	cp $(addprefix $(VPATH)/,$(dist_noinst_SCRIPTS)) . || true
	touch $@

if HAVE_MAGICK
with_imagemagick = yes
else
with_imagemagick = no
endif

if MINGW
if HAVE_MAGICK
lib_LTLIBRARIES = eye4graphics.la
eye4graphics_la_SOURCES = eye4graphics.cc
eye4graphics_la_CPPFLAGS = $(MAGICK_CFLAGS)
eye4graphics_la_LDFLAGS = -module  $(MAGICK_LIBS) -no-undefined -avoid-version -shared
endif
else
# extensions
dist_noinst_SCRIPTS += \
	eye4graphics.cc \
	eye4graphics.h
# end of extensions
all-local: utils_installer eye4graphics.cc eye4graphics.h
	VPATH='$(VPATH)' CC='$(CXX)' PKG_CONFIG='$(PKG_CONFIG)' with_imagemagick='$(with_imagemagick)' $(PYTHON) setup.py build

install-exec-local:
	with_imagemagick='$(with_imagemagick)' $(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PYTHON_PREFIX)
endif
