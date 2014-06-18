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
	fmbt-parallel		\
	fmbt-trace-share	\
	fmbt-stats		\
	fmbt-view		\
	remote_pyaal		\
	remote_python
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
	fmbtparsers.py		\
	fmbttizen-agent.py	\
	fmbttizen.py		\
	fmbtuinput.py		\
	fmbtvnc.py		\
	fmbtweb.py		\
	fmbtwindows.py		\
	fmbtwindows_agent.py	\
	fmbtx11.py		\
	fmbtx11_conn.py		\
	lsts.py
# end of modules

# extensions
dist_noinst_SCRIPTS += \
	eye4graphics.cc \
	eye4graphics.h
# end of extensions

all-local: eye4graphics.cc eye4graphics.h
	$(PYTHON) setup.py build

install-exec-local:
	$(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PYTHON_PREFIX)
