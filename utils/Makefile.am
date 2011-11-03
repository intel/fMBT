if HAVE_PYTHON

PYTHON_WRAPPERS = wrapperdir/fmbt-gt wrapperdir/fmbt-log wrapperdir/lsts2dot
CLEANFILES = $(PYTHON_WRAPPERS)

wrapperdir:
	$(MKDIR_P) $@

$(PYTHON_WRAPPERS): wrapperdir ../config.status
	@echo Generating $@...
	@echo '#!/bin/sh' > $@
	@echo 'exec $(PYTHON) $(pkgpythondir)/'$$(basename $@)' "$$@"' >> $@

dist_bin_SCRIPTS = $(PYTHON_WRAPPERS) fmbt-view

pkgpython_PYTHON = lsts.py fmbt-gt fmbt-log lsts2dot

dist_noinst_SCRIPTS = parallel rextendedrules.py

endif
