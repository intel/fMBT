if HAVE_PYTHON

PYTHON_WRAPPERS = wrapperdir/fmbt-gt wrapperdir/fmbt-editor wrapperdir/fmbt-gteditor wrapperdir/fmbt-log wrapperdir/lsts2dot wrapperdir/fmbt-parallel wrapperdir/fmbt-stats wrapperdir/remote_pyaal wrapperdir/remote_python
CLEANFILES = $(PYTHON_WRAPPERS)

wrapperdir:
	$(MKDIR_P) $@

$(PYTHON_WRAPPERS): wrapperdir ../config.status
	@echo Generating $@...
	@echo '#!/bin/sh' > $@
	@echo 'LD_LIBRARY_PATH=$$LD_LIBRARY_PATH:$(pkgpythondir) exec $(PYTHON) $(pkgpythondir)/'$$(basename $@)' "$$@"' >> $@

dist_bin_SCRIPTS = $(PYTHON_WRAPPERS) fmbt-view remote_exec.sh

pkgpython_PYTHON = aalmodel.py lsts.py fmbtparsers.py fmbt-editor fmbt-gt fmbt-gteditor fmbt-log fmbt-stats lsts2dot fmbt-parallel remote_pyaal remote_python fmbt_config.py

python_PYTHON = fmbtweb.py fmbt.py eyenfinger.py

endif
