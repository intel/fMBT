LOCAL_ADAPTERS = adapter.cc awrapper.cc adapter_model.cc adapter_mapper.cc adapter_dummy.cc adapter_timer.cc adapter_lib.cc

LOCAL_HEURISTICS =  heuristic.cc heuristic_random.cc heuristic_mrandom.cc heuristic_greedy.cc

LOCAL_COVERAGES = coverage.cc coverage_mapper.cc coverage_tree.cc coverage_prop.cc

LOCAL_MODELS = model.cc mwrapper.cc lts.cc model_lib.cc

COMMON_SOURCES = fmbt.cc test_engine.cc log.cc helper.cc lts.g.d_parser.cc xrules.g.d_parser.cc lts_xrules.cc  $(LOCAL_ADAPTERS) $(LOCAL_HEURISTICS) $(LOCAL_COVERAGES) $(LOCAL_MODELS) conf.g.d_parser.cc conf.cc mrules.g.d_parser.cc policy.cc alg_bdfs.cc history.cc end_condition.cc null.cc

fmbt_SOURCES                  = $(COMMON_SOURCES) adapter_dlopen.cc adapter_remote.cc lts_remote.cc lts_trace.cc xrules_remote.cc covlang.g.d_parser.cc coverage_market.cc coverage_tema_seq.cc history_remote.cc

fmbt_droid_SOURCES            = $(COMMON_SOURCES)

fmbt_aalc_SOURCES = lang.g.d_parser.cc lang.cc helper.cc aalang_cpp.cc aalang_py.cc

remote_adapter_loader_SOURCES = remote_adapter_loader.cc adapter.cc log.cc adapter_dummy.cc adapter_model.cc adapter_v4l2.cc helper.cc model.cc

fmbt_cparsers_la_SOURCES      = xrules.g.d_parser.cc lts.g.d_parser.cc helper.cc

fmbt_aalp_SOURCES = aalp.ll
