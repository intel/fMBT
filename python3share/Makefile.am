dist_man_MANS = \
	man/python3share-server.1 \
	man/python3share-client.1

dist_noinst_SCRIPTS = \
	setup.py		 \
	python3share-client      \
	python3share-server      \
	python3share/__init__.py \
	python3share/client.py	 \
	python3share/server.py	 \
	python3share/messages.py

install-exec-local:
	$(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PYTHON_PREFIX)

pythonshare_installer: $(dist_noinst_SCRIPTS)
	cp $? . || true
	touch $@
