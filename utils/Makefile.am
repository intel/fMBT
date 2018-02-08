VPATH ?= .

dist_noinst_SCRIPTS = \
	setup.py

# scripts
dist_noinst_SCRIPTS +=		\
	fmbt-gt			\
	fmbt-editor		\
	fmbt-scripter		\
	fmbt-debug		\
	fmbt-gteditor		\
	fmbt-log		\
	lsts2dot		\
	fmbt-trace-share	\
	fmbt-stats		\
	fmbt-view		\
	remote_pyaal		\
    remote_rbaal		\
	remote_python           \
	remote_exec.sh
# end of scripts

# modules
dist_noinst_SCRIPTS +=		\
	aalmodel.py		\
	eyenfinger.py		\
	fmbt.py			\
	fmbt_config.py		\
	fmbtandroid.py		\
	fmbtchromiumos.py	\
	fmbtgti.py		\
	fmbtlogger.py		\
	fmbtpng.py     	        \
	fmbttizen-agent.py	\
	fmbttizen.py		\
	fmbtuinput.py		\
	fmbtvnc.py		\
	fmbtweb.py		\
	fmbtwindows.py		\
	fmbtwindows_agent.py	\
	fmbtx11.py		\
	fmbtx11_conn.py		\
	lsts.py                 \
	pycosh.py
# end of modules

utils_installer: $(dist_noinst_SCRIPTS)
	cp $(addprefix $(VPATH)/,$(dist_noinst_SCRIPTS)) . || true
	touch $@

if MINGW
if HAVE_MAGICK
lib_LTLIBRARIES = eye4graphics.la
eye4graphics_la_SOURCES = eye4graphics.cc
eye4graphics_la_CPPFLAGS = $(MAGIC_CFLAGS)
eye4graphics_la_LDFLAGS = -module  $(MAGIC_LIBS) -no-undefined -avoid-version -shared
endif
else
# extensions
dist_noinst_SCRIPTS += \
	eye4graphics.cc \
	eye4graphics.h
# end of extensions
all-local: utils_installer eye4graphics.cc eye4graphics.h
	VPATH='$(VPATH)' CC='$(CXX)' PKG_CONFIG='$(PKG_CONFIG)' $(PYTHON) setup.py build

install-exec-local:
	$(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PYTHON_PREFIX)
endif
