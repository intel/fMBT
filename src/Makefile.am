if ANDROID
bin_PROGRAMS = fmbt_droid
else
bin_PROGRAMS = fmbt remote_adapter_loader
endif

if HAVE_PYTHON
dist_bin_SCRIPTS = remote_python
endif

LOCAL_ADAPTERS = adapter_model.cc adapter_mapper.cc adapter_dlopen.cc adapter_dummy.cc # disabled-missing: adapter_timer.cc

COMMON_SOURCES = fmbt.cc lts.cc test_engine.cc heuristic_random.cc log.cc helper.cc lts.g.d_parser.cc xrules.g.d_parser.cc lts_xrules.cc coverage_market.cc coverage_mapper.cc covlang.g.d_parser.cc heuristic_greedy.cc coverage_tree.cc model.cc heuristic.cc coverage.cc adapter.cc $(LOCAL_ADAPTERS) conf.g.d_parser.cc conf.cc mrules.g.d_parser.cc policy.cc

fmbt_SOURCES       = $(COMMON_SOURCES) adapter_remote.cc

fmbt_droid_SOURCES = $(COMMON_SOURCES)

remote_adapter_loader_SOURCES = remote_adapter_loader.cc adapter.cc log.cc adapter_dummy.cc adapter_model.cc adapter_v4l2.cc helper.cc model.cc

noinst_HEADERS = adapter_dlopen.hh adapter_dummy.hh adapter_mapper.hh adapter_model.hh adapter_remote.hh adapter_v4l2.hh adapter_xrules.hh conf.hh coverage.hh coverage_mapper.hh coverage_market.hh coverage_tree.hh helper.hh heuristic_greedy.hh heuristic.hh heuristic_random.hh log_null.hh lts.hh lts_remote.hh lts_xrules.hh model.hh policy.hh rules.hh test_engine.hh

pkginclude_HEADERS=adapter.hh factory.hh writable.hh log.hh

noinst_HEADERS += conf.g lts.g mrules.g covlang.g xrules.g

fmbt_CPPFLAGS       = -Wall -g -O0 -fPIC -I ./$(VPATH)/d -I `pwd` `pkg-config --cflags libedit glib-2.0 gobject-2.0`
fmbt_droid_CPPFLAGS = -Wall -g -O0 -I d -I `pwd` `pkg-config --cflags libedit` -DDROI
remote_adapter_loader_CPPFLAGS = -Wall -g -I d -DDROI

fmbt_LDFLAGS       = -g `pkg-config --libs glib-2.0 gobject-2.0 libedit` -lboost_regex -Wl,-E -ldl
fmbt_droid_LDFLAGS = -g -ledit
remote_adapter_loader_LDFLAGS = -g

fmbt_LDADD       = d/libdparse.a
fmbt_droid_LDADD = d/libdparse.a
remote_adapter_loader_LDADD = d/libdparse.a

dsources = d/baseline d/BUILD_VERSION d/calc d/CHANGES d/COPYRIGHT d/Makefile d/parser_tests d/README d/arg.h d/d.h d/dparse.h d/dparse_tables.h d/dparse_tree.h d/dsymtab.h d/gramgram.h d/gram.h d/lex.h d/lr.h d/mkdparse.h d/parse.h d/read_binary.h d/scan.h d/util.h d/write_tables.h d/arg.c d/dparse_tree.c d/driver_parsetree.c d/gram.c d/grammar.g.c d/lex.c d/lr.c d/make_dparser.c d/mkdparse.c d/my.c d/parse.c d/read_binary.c d/sample_parser.c d/scan.c d/symtab.c d/test_parser.c d/util.c d/version.c d/write_tables.c d/4calc.g d/C.g d/my.g d/sample.g d/faq.html d/index.html d/manual.html d/make_dparser.1 d/make_dparser.cat

noinst_HEADERS += $(dsources)

d/make_dparser:
	(mkdir d 2>/dev/null && cp -r $(VPATH)/d .) || true # qnd way to for VPATH build
	cd d; $(MAKE) make_dparser

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

# coverage_market.o: coverage_market.hh
