dist_man_MANS = \
	man/pythonshare-server.1 \
	man/pythonshare-client.1

dist_noinst_SCRIPTS = \
	setup.py		\
	pythonshare-client      \
	pythonshare-server      \
	pythonshare/__init__.py \
	pythonshare/client.py	\
	pythonshare/server.py	\
	pythonshare/messages.py

install-exec-local:
	$(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PYTHON_PREFIX)
