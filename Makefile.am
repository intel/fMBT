ACLOCAL_AMFLAGS = -I m4

SUBDIRS = utils src test examples

dist_doc_DATA = \
	README			\
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
