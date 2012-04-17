if HAVE_PYTHON

PYTHON_WRAPPERS = wrapperdir/fmbt-gt wrapperdir/fmbt-gteditor wrapperdir/fmbt-log wrapperdir/lsts2dot wrapperdir/fmbt-parallel wrapperdir/fmbt-stats
CLEANFILES = $(PYTHON_WRAPPERS)

wrapperdir:
	$(MKDIR_P) $@

$(PYTHON_WRAPPERS): wrapperdir ../config.status
	@echo Generating $@...
	@echo '#!/bin/sh' > $@
	@echo 'LD_LIBRARY_PATH=$$LD_LIBRARY_PATH:$(pkgpythondir) exec $(PYTHON) $(pkgpythondir)/'$$(basename $@)' "$$@"' >> $@

dist_bin_SCRIPTS = $(PYTHON_WRAPPERS) fmbt-view

pkgpython_PYTHON = lsts.py fmbtparsers.py fmbt-gt fmbt-gteditor fmbt-log fmbt-stats lsts2dot fmbt-parallel

endif
