if MINGW
bin_PROGRAMS = remote_pyaal fmbt-editor fmbt-view fmbt-log fmbt-stats lsts2dot fmbt-scripter fmbt-debug fmbt-trace-share

AM_CFLAGS = $(GLIB_CFLAGS)
AM_LDFLAGS = $(GLIB_LIBS)

remote_pyaal_SOURCES		= exec_wrapper.c
fmbt_editor_SOURCES		= exec_wrapper.c
fmbt_view_SOURCES		= exec_wrapper.c
fmbt_stats_SOURCES		= exec_wrapper.c
fmbt_log_SOURCES		= exec_wrapper.c
lsts2dot_SOURCES		= exec_wrapper.c
fmbt_scripter_SOURCES		= exec_wrapper.c
fmbt_debug_SOURCES		= exec_wrapper.c
fmbt_trace_share_SOURCES	= exec_wrapper.c
endif

ACLOCAL_AMFLAGS = -I m4

SUBDIRS = utils3 src python3share test examples

dist_doc_DATA = \
	README			\
	README-windows.txt      \
	doc/aal_python.txt      \
	doc/adapters.txt	\
	doc/architecture.txt	\
	doc/configuration.txt   \
	doc/tutorial.txt

dist_man_MANS =                 \
        man/fmbt-aalc.1         \
        man/fmbt-aalp.1         \
        man/fmbt-view.1         \
        man/fmbt-scripter.1     \
        man/fmbt.1              \
        man/fmbt-gt.1           \
        man/fmbt-log.1          \
        man/fmbt-trace-share.1  \
        man/fmbt-editor.1       \
        man/remote_pyaal.1

src/android/fmbt_droid:
	$(MAKE) -C src android/fmbt_droid
