if ANDROID
bin_PROGRAMS = fmbt_droid
ANDROID_NDK_BUILD = ndk-build
else
bin_PROGRAMS = fmbt remote_adapter_loader lang
endif

if HAVE_PYTHON
dist_bin_SCRIPTS = remote_python
pkgpyexec_LTLIBRARIES = fmbt_cparsers.la
endif

LOCAL_ADAPTERS = adapter.cc awrapper.cc adapter_model.cc adapter_mapper.cc adapter_dummy.cc adapter_timer.cc

LOCAL_HEURISTICS =  heuristic.cc heuristic_random.cc heuristic_mrandom.cc heuristic_greedy.cc

LOCAL_COVERAGES = coverage.cc coverage_mapper.cc coverage_tree.cc coverage_prop.cc

COMMON_SOURCES = fmbt.cc mwrapper.cc lts.cc test_engine.cc log.cc helper.cc lts.g.d_parser.cc xrules.g.d_parser.cc lts_xrules.cc model.cc $(LOCAL_ADAPTERS) $(LOCAL_HEURISTICS) $(LOCAL_COVERAGES) conf.g.d_parser.cc conf.cc mrules.g.d_parser.cc policy.cc alg_bdfs.cc history.cc

fmbt_SOURCES                  = $(COMMON_SOURCES) adapter_dlopen.cc adapter_remote.cc adapter_lib.cc model_lib.cc lts_remote.cc lts_trace.cc xrules_remote.cc covlang.g.d_parser.cc coverage_market.cc coverage_tema_seq.cc history_remote.cc

fmbt_droid_SOURCES            = $(COMMON_SOURCES)

lang_SOURCES = lang.g.d_parser.cc lang.cc helper.cc aalang_cpp.cc aalang_py.cc

remote_adapter_loader_SOURCES = remote_adapter_loader.cc adapter.cc log.cc adapter_dummy.cc adapter_model.cc adapter_v4l2.cc helper.cc model.cc

fmbt_cparsers_la_SOURCES      = xrules.g.d_parser.cc lts.g.d_parser.cc helper.cc

noinst_HEADERS = adapter_dlopen.hh adapter_dummy.hh adapter_mapper.hh adapter_model.hh adapter_remote.hh adapter_v4l2.hh adapter_xrules.hh conf.hh coverage.hh coverage_mapper.hh coverage_market.hh coverage_tree.hh coverage_tema_seq.hh helper.hh heuristic_greedy.hh heuristic.hh heuristic_minerror.hh heuristic_random.hh log_null.hh lts.hh lts_remote.hh lts_xrules.hh xrules_remote.hh model.hh policy.hh rules.hh test_engine.hh alg_bdfs.hh

pkginclude_HEADERS = adapter.hh factory.hh writable.hh log.hh aal.hh model.hh awrapper.hh mwrapper.hh alphabet.hh

noinst_HEADERS += conf.g lts.g mrules.g covlang.g xrules.g lang.g

fmbt_CPPFLAGS                  = -Wall -g -O0 -fPIC -I ./$(VPATH)/d -I `pwd` `pkg-config --cflags libedit glib-2.0 gobject-2.0`
fmbt_droid_CPPFLAGS            = -Wall -g -O0 -I d -I `pwd` `pkg-config --cflags libedit` -DDROI
fmbt_android_CPPFLAGS          = -Wall -g -O0 -I jni/d -I `pwd` `pkg-config --cflags libedit` -DDROI
remote_adapter_loader_CPPFLAGS = -Wall -g -I d -DDROI
fmbt_cparsers_la_CPPFLAGS      = -Wall -g -O0 -fPIC -I ./$(VPATH)/d -I `pwd` `pkg-config --cflags libedit glib-2.0 gobject-2.0` -DCAPI
lang_CPPFLAGS		       = -Wall -g -O0 -fPIC -I ./$(VPATH)/d -I `pwd` `pkg-config --cflags libedit glib-2.0 gobject-2.0`

fmbt_LDFLAGS                   = -g `pkg-config --libs glib-2.0 gobject-2.0 libedit` -lboost_regex -Wl,-E -ldl
fmbt_droid_LDFLAGS             = -g -ledit
fmbt_cparsers_la_LDFLAGS       = -g `pkg-config --libs glib-2.0 gobject-2.0 libedit` -lboost_regex -Wl,-E -ldl -avoid-version -module -shared -export-dynamic
remote_adapter_loader_LDFLAGS  = -g
lang_LDFLAGS		       = -g `pkg-config --libs glib-2.0 gobject-2.0 libedit` -lboost_regex -Wl,-E -ldl

fmbt_LDADD                     = d/libdparse.a
fmbt_droid_LDADD               = d/libdparse.a
fmbt_cparsers_la_LIBADD        = d/libdparse.a
remote_adapter_loader_LDADD    = d/libdparse.a
lang_LDADD                     = d/libdparse.a

dsources = d/baseline d/BUILD_VERSION d/calc d/CHANGES d/COPYRIGHT d/Makefile d/parser_tests d/README d/arg.h d/d.h d/dparse.h d/dparse_tables.h d/dparse_tree.h d/dsymtab.h d/gramgram.h d/gram.h d/lex.h d/lr.h d/mkdparse.h d/parse.h d/read_binary.h d/scan.h d/util.h d/write_tables.h d/arg.c d/dparse_tree.c d/driver_parsetree.c d/gram.c d/grammar.g.c d/lex.c d/lr.c d/make_dparser.c d/mkdparse.c d/my.c d/parse.c d/read_binary.c d/sample_parser.c d/scan.c d/symtab.c d/test_parser.c d/util.c d/version.c d/write_tables.c d/4calc.g d/C.g d/my.g d/sample.g d/faq.html d/index.html d/manual.html d/make_dparser.1 d/make_dparser.cat

noinst_HEADERS += $(dsources)

d/make_dparser d/libdparse.a:
	(mkdir d 2>/dev/null && cp -r $(VPATH)/d .) || true # qnd way to for VPATH build
	cd d; $(MAKE) make_dparser libdparse.a

lang.g.d_parser.cc: lang.g d/make_dparser
	d/make_dparser -o lang.g.d_parser.cc -i lang ./$(VPATH)/lang.g

mrules.g.d_parser.cc: mrules.g d/make_dparser
	d/make_dparser -o mrules.g.d_parser.cc -i mrules ./$(VPATH)/mrules.g

conf.g.d_parser.cc: conf.g d/make_dparser
	d/make_dparser -o conf.g.d_parser.cc -i conf ./$(VPATH)/conf.g

lts.g.d_parser.cc: lts.g d/make_dparser
	d/make_dparser -o lts.g.d_parser.cc -i lts ./$(VPATH)/lts.g

xrules.g.d_parser.cc: xrules.g d/make_dparser
	d/make_dparser -o xrules.g.d_parser.cc -i xrules ./$(VPATH)/xrules.g

xrules_extended.g.d_parser.cc: xrules_extended.g d/make_dparser
	d/make_dparser -o xrules_extended.g.d_parser.cc -i xrules_extended ./$(VPATH)/xrules_extended.g

covlang.g.d_parser.cc: covlang.g d/make_dparser
	d/make_dparser -o covlang.g.d_parser.cc -i covlang ./$(VPATH)/covlang.g

fmbt_android:
	bash -c 'rm -rf android; mkdir android; cd android; ln -s .. jni'
	@echo 'APP_STL := stlport_static'			> Application.mk

	@echo 'LOCAL_PATH := $$(call my-dir)'			> Android.mk
	@echo 'include $$(CLEAR_VARS)'				>> Android.mk
	@echo 'LOCAL_MODULE    := fmbt_android'			>> Android.mk
	@echo 'LOCAL_SRC_FILES := $(fmbt_droid_SOURCES)'	>> Android.mk
	@echo 'LOCAL_CPPFLAGS  := $(fmbt_android_CPPFLAGS)'	>> Android.mk
	@echo 'LOCAL_CPP_EXTENSION := .cc'			>> Android.mk
	@echo 'include $$(BUILD_EXECUTABLE)'			>> Android.mk
	bash -c 'cd android; $(ANDROID_NDK_BUILD) V=1'


# coverage_market.o: coverage_market.hh
