if ANDROID
bin_PROGRAMS = fmbt_droid
else
bin_PROGRAMS = fmbt remote_adapter_loader fmbt-aalc fmbt-aalp fmbt-ucheck fmbt-log2lsts
endif

if HAVE_PYTHON
pkgpyexec_LTLIBRARIES = fmbt_cparsers.la
endif

FMBTBUILDINFOCFLAGS=-DFMBTBUILDINFO='"@FMBTBUILDINFO@"'

##########################################
# Define all sources in Sources.mk so that
# the definitions can be shared between
# Autotools and Android makefiles

include Sources.mk

noinst_HEADERS =  aalang.hh aalang_cpp.hh aalang_java.hh aalang_py.hh adapter_rly08btech.hh adapter_dlopen.hh adapter_dummy.hh adapter_mapper.hh adapter_model.hh adapter_remote.hh adapter_timer.hh adapter_v4l2.hh alg_bdfs.hh conf.hh coverage.hh coverage_proxy.hh coverage_exec_filter.hh coverage_join.hh coverage_include.hh coverage_mapper.hh coverage_market.hh coverage_of.hh coverage_prop.hh coverage_report.hh coverage_tema_seq.hh coverage_tree.hh end_condition.hh helper.hh heuristic_proxy.hh heuristic_include.hh heuristic_greedy.hh heuristic.hh heuristic_minerror.hh heuristic_mrandom.hh heuristic_random.hh history.hh history_glob.hh history_log.hh history_multi.hh history_remote.hh log_null.hh lts.hh lts_remote.hh lts_trace.hh lts_xrules.hh model.hh model_remote.hh null.hh of.hh of_csv.hh of_html.hh of_null.hh policy.hh rules.hh test_engine.hh xrules_remote.hh model_yes.hh aal_remote.hh coverage_uniq.hh coverage_set.hh heuristic_weight.hh coverage_avoid.hh coverage_trace.hh coverage_min.hh coverage_const.hh alphabet_impl.hh endhook.hh coverage_paths.hh model_filter.hh coverage_include.hh remote.hh coverage_end_condition.hh coverage_if.hh coverage_shared.hh coverage_short.hh coverage_notice.hh coverage_report_filter.hh coverage_restart.hh aalang_tag.hh aalang_action.hh model_cshared.hh coverage_nohistory.hh random.hh random_c.hh random_intel_hw.hh random_devrandom.hh random_supported.hh function.hh function_pid.hh function_const.hh function_time.hh function_ustime.hh function_supported.hh heuristic_coverage_random.hh coverage_random.hh proxy.hh

pkginclude_HEADERS = aal.hh adapter.hh alphabet.hh awrapper.hh factory.hh helper.hh log.hh model.hh mwrapper.hh params.hh reffable.hh verdict.hh writable.hh

noinst_HEADERS += conf.g lts.g mrules.g covlang.g xrules.g lang.g uconf.g filter.g weight.g set.g paths.g

noinst_HEADERS += Android.mk Application.mk
if RDRND
AM_CXXFLAGS = -mrdrnd
endif

fmbt_CPPFLAGS                  = -Wall -pedantic -fPIC -I ./d -I `pwd` $(LIBEDIT_CFLAGS) $(GLIB_CFLAGS) $(GOBJECT_CFLAGS) $(XML2_CFLAGS)  $(JVMCFLAGS) $(FMBTBUILDINFOCFLAGS)
fmbt_ucheck_CPPFLAGS	       = -Wall -pedantic -fPIC -I ./d -I `pwd` $(LIBEDIT_CFLAGS) $(GLIB_CFLAGS) $(GOBJECT_CFLAGS) $(XML2_CFLAGS) $(FMBTBUILDINFOCFLAGS)
fmbt_droid_CPPFLAGS            = -Wall -pedantic -fPIC -I d -I `pwd` -DDROI $(FMBTBUILDINFOCFLAGS)
remote_adapter_loader_CPPFLAGS = -Wall -pedantic -I d -DDROI $(FMBTBUILDINFOCFLAGS) $(GLIB_CFLAGS)
fmbt_cparsers_la_CPPFLAGS      = -Wall -pedantic -fPIC -I ./d -I `pwd` $(LIBEDIT_CFLAGS) $(GLIB_CFLAGS) $(GOBJECT_CFLAGS) -DCAPI $(FMBTBUILDINFOCFLAGS)
fmbt_aalc_CPPFLAGS	       = -Wall -pedantic -fPIC -I ./d -I `pwd` $(LIBEDIT_CFLAGS) $(GLIB_CFLAGS) $(GOBJECT_CFLAGS) -DINCDIR=\"${pkgincludedir}\" $(FMBTBUILDINFOCFLAGS)
fmbt_aalp_CPPFLAGS	       = $(FMBTBUILDINFOCFLAGS) $(GLIB_CFLAGS)
fmbt_log2lsts_CPPFLAGS	       = -Wall -pedantic -fPIC -I d -I `pwd` $(LIBEDIT_CFLAGS) $(GLIB_CFLAGS) $(GOBJECT_CFLAGS) $(XML2_CFLAGS) $(FMBTBUILDINFOCFLAGS)

fmbt_LDFLAGS                   = -g $(JVMLDFLAGS) $(XML2_LIBS) $(GLIB_LIBS) $(GOBJECT_LIBS) $(LIBEDIT_LIBS) -lboost_regex -Wl,-E -ldl
fmbt_ucheck_LDFLAGS            = -g $(XML2_LIBS) $(GLIB_LIBS) $(GOBJECT_LIBS) $(LIBEDIT_LIBS) -lboost_regex -Wl,-E -ldl
fmbt_droid_LDFLAGS             = -Wl,-E -ldl
fmbt_cparsers_la_LDFLAGS       = -g $(GLIB_LIBS) $(GOBJECT_LIBS) $(LIBEDIT_LIBS) -lboost_regex -Wl,-E -ldl -avoid-version -module -shared -export-dynamic
remote_adapter_loader_LDFLAGS  = -g -ldl $(GLIB_LIBS)
fmbt_aalc_LDFLAGS	       = -g $(XML2_LIBS) $(GLIB_LIBS) $(GOBJECT_LIBS) -lboost_regex -Wl,-E -ldl
fmbt_aalp_LDFLAGS	       = -g $(GLIB_LIBS) -lboost_regex -ldl
fmbt_log2lsts_LDFLAGS 	       = -g $(XML2_LIBS) $(GLIB_LIBS) $(GOBJECT_LIBS) $(LIBEDIT_LIBS) -lboost_regex -Wl,-E -ldl

fmbt_LDADD                     = d/libdparse.a
fmbt_ucheck_LDADD              = d/libdparse.a
fmbt_droid_LDADD               = d/libdparse.a
fmbt_cparsers_la_LIBADD        = d/libdparse.a
remote_adapter_loader_LDADD    = d/libdparse.a -lrt
fmbt_aalc_LDADD                = d/libdparse.a
fmbt_log2lsts_LDADD   	       = d/libdparse.a

dsources = d/baseline d/BUILD_VERSION d/calc d/CHANGES d/COPYRIGHT d/Makefile d/parser_tests d/README d/arg.h d/d.h d/dparse.h d/dparse_tables.h d/dparse_tree.h d/dsymtab.h d/gramgram.h d/gram.h d/lex.h d/lr.h d/mkdparse.h d/parse.h d/read_binary.h d/scan.h d/util.h d/write_tables.h d/arg.c d/dparse_tree.c d/driver_parsetree.c d/gram.c d/grammar.g.c d/lex.c d/lr.c d/make_dparser.c d/mkdparse.c d/my.c d/parse.c d/read_binary.c d/sample_parser.c d/scan.c d/symtab.c d/test_parser.c d/util.c d/version.c d/write_tables.c d/4calc.g d/C.g d/my.g d/sample.g d/faq.html d/index.html d/manual.html d/make_dparser.1 d/make_dparser.cat

noinst_HEADERS += $(dsources)

d/libdparse.a:
	(mkdir d 2>/dev/null && cp -r d .) || true # qnd way to for VPATH build
	cd d; $(MAKE) make_dparser libdparse.a

# Building d/libdparse.a creates make_dparser, too. On the other hand,
# building only d/make_dparser produces d/libdparse.a as well. Running
# run two build processes (one for d/make_dparser, the other for
# d/libdparse.a) concurrently may acuse errors. Therefore the
# following rules depend on d/libdparse.a, yet they need
# d/make_dparser.
weight.g.d_parser.cc: weight.g d/libdparse.a
	d/make_dparser -o weight.g.d_parser.cc -i weight ./weight.g

lang.g.d_parser.cc: lang.g d/libdparse.a
	d/make_dparser -o lang.g.d_parser.cc -i lang ./lang.g

mrules.g.d_parser.cc: mrules.g d/libdparse.a
	d/make_dparser -o mrules.g.d_parser.cc -i mrules ./mrules.g

conf.g.d_parser.cc: conf.g d/libdparse.a
	d/make_dparser -o conf.g.d_parser.cc -i conf ./conf.g

lts.g.d_parser.cc: lts.g d/libdparse.a
	d/make_dparser -o lts.g.d_parser.cc -i lts ./lts.g

xrules.g.d_parser.cc: xrules.g d/libdparse.a
	d/make_dparser -o xrules.g.d_parser.cc -i xrules ./xrules.g

xrules_extended.g.d_parser.cc: xrules_extended.g d/libdparse.a
	d/make_dparser -o xrules_extended.g.d_parser.cc -i xrules_extended ./xrules_extended.g

covlang.g.d_parser.cc: covlang.g d/libdparse.a
	d/make_dparser -A -o covlang.g.d_parser.cc -i covlang ./covlang.g

uconf.g.d_parser.cc: uconf.g d/libdparse.a
	d/make_dparser -o uconf.g.d_parser.cc -i uconf ./uconf.g

filter.g.d_parser.cc: filter.g d/libdparse.a
	d/make_dparser -o filter.g.d_parser.cc -i filter ./filter.g

set.g.d_parser.cc: set.g d/libdparse.a
	d/make_dparser -o set.g.d_parser.cc -i set ./set.g

paths.g.d_parser.cc: paths.g d/libdparse.a
	d/make_dparser -o paths.g.d_parser.cc -i paths ./paths.g

clean-local:
	(cd d; make clean)

##########################################
# Building fmbt_android with Android NDK

# Application.mk: Makefile
# 	@echo 'APP_STL := stlport_static'		> $@
# 	@echo 'APP_MODULES := dparse_droid fmbt_droid'	>> $@
# 	@echo 'APP_OPTIM := debug'			>> $@

# Android.mk: Makefile
# 	@echo 'LOCAL_PATH := $$(call my-dir)'				> $@
# 	@echo '############################## MODULE 1: dparse_droid'	>> $@
# 	@echo 'include $$(CLEAR_VARS)'					>> $@
# 	@echo 'LOCAL_MODULE := dparse_droid'				>> $@
# 	@echo 'LOCAL_SRC_FILES := $$(subst jni/,,$$(wildcard jni/d/*.c))'			>> $@
# 	@echo 'LOCAL_CFLAGS := -DD_MAJOR_VERSION=1 -DD_MINOR_VERSION=26 -DD_BUILD_VERSION=\"\"'	>> $@
# 	@echo 'include $$(BUILD_STATIC_LIBRARY)'			>> $@
# 	@echo '############################## MODULE 2: fmbt_droid'	>> $@
# 	@echo 'include $$(CLEAR_VARS)'					>> $@
# 	@echo 'LOCAL_MODULE    := fmbt_droid'				>> $@
# 	@echo 'LOCAL_SRC_FILES := $(fmbt_droid_SOURCES)'		>> $@
# 	@echo 'LOCAL_CPPFLAGS  := -Ijni/d $(fmbt_droid_CPPFLAGS)'	>> $@
# 	@echo 'LOCAL_STATIC_LIBRARIES := dparse_droid'			>> $@
# 	@echo 'LOCAL_LDLIBS := -ldl -llog'				>> $@
# 	@echo 'LOCAL_LDFLAGS := -Wl,-E -Wl,--no-gc-sections'		>> $@
# 	@echo 'LOCAL_CPP_EXTENSION := .cc'				>> $@
# 	@echo 'include $$(BUILD_EXECUTABLE)'				>> $@

# android/fmbt_droid: Application.mk Android.mk $(fmbt_droid_SOURCES)
# 	bash -c 'mkdir -p android; cd android; [ -s jni ] || ln -s .. jni; echo "target=android-5" > default.properties'
# 	bash -c 'cd android; rm -f fmbt_droid; nice @NDK_BUILD@ -j4 && ln libs/*/fmbt_droid .'

android/fmbt_droid: Android.mk $(fmbt_droid_SOURCES)
	bash -c 'mkdir -p android; cd android; [ -s jni ] || ln -s .. jni; echo "target=android-5" > default.properties'
	bash -c 'cd android; rm -f fmbt_droid; nice @NDK_BUILD@ -j4 && ln libs/*/fmbt_droid .'

##########################################
# How to build an AAL/C++ adapter/model (adel) for Android?
# 1. Convert AAL to C++:
#    fmbt-aalc adel.aal -o adel.cc
# 2. Write Android.mk:
# include $(CLEAR_VARS)
# LOCAL_MODULE := adel
# LOCAL_MODULE_FILENAME := adel
# LOCAL_SRC_FILES := adel.cc
# LOCAL_CPPFLAGS  := -Wall -DDROI
# LOCAL_ALLOW_UNDEFINED_SYMBOLS := true
# LOCAL_CPP_EXTENSION := .cc
# include $(BUILD_SHARED_LIBRARY)
# 3. ndk-build
