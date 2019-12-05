LOCAL_ADAPTERS = adapter.cc awrapper.cc adapter_model.cc adapter_mapper.cc adapter_dummy.cc adapter_timer.cc adapter_lib.cc adapter_rly08btech.cc

LOCAL_HEURISTICS =  heuristic.cc heuristic_random.cc heuristic_mrandom.cc heuristic_greedy.cc weight.g.d_parser.cc heuristic_weight.cc heuristic_include.cc heuristic_coverage_random.cc coverage_random.cc

LOCAL_COVERAGES = coverage.cc coverage_exec_filter.cc coverage_mapper.cc coverage_tree.cc coverage_prop.cc coverage_uniq.cc filter.g.d_parser.cc set.g.d_parser.cc coverage_set.cc coverage_avoid.cc coverage_trace.cc coverage_min.cc coverage_const.cc coverage_paths.cc coverage_report.cc paths.g.d_parser.cc coverage_include.cc coverage_join.cc coverage_end_condition.cc coverage_if.cc coverage_short.cc covlang.g.d_parser.cc coverage_market.cc coverage_restart.cc coverage_nohistory.cc coverage_proxy.cc heuristic_proxy.cc

LOCAL_MODELS = model.cc mwrapper.cc lts.cc lts.g.d_parser.cc model_lib.cc model_yes.cc

COMMON_SOURCES = fmbt.cc test_engine.cc log.cc helper.cc xrules.g.d_parser.cc lts_xrules.cc  $(LOCAL_ADAPTERS) $(LOCAL_HEURISTICS) $(LOCAL_COVERAGES) $(LOCAL_MODELS) conf.g.d_parser.cc conf.cc mrules.g.d_parser.cc policy.cc alg_bdfs.cc history.cc end_condition.cc date.g.d_parser.cc null.cc aal.cc endhook.cc coverage_of.cc  random.cc random_c.cc random_devrandom.cc random_supported.cc function.cc function_pid.cc function_const.cc function_time.cc function_ustime.cc params.cc function_supported.cc learning.cc learn_time.cc learn_action.cc learn_proxy.cc readline_wrapper.cc verdict.cc

if RDRND
COMMON_SOURCES += random_intel_hw.hh
endif

fmbt_SOURCES                  = $(COMMON_SOURCES) adapter_dlopen.cc adapter_remote.cc lts_remote.cc lts_trace.cc xrules_remote.cc coverage_shared.cc coverage_tema_seq.cc history_remote.cc model_remote.cc aal_java.cc aal_remote.cc history_log.cc history_multi.cc history_glob.cc remote.cc learn_function.cc function_random.cc function_array.cc

fmbt_ucheck_SOURCES	      = uc.cc helper.cc log.cc xrules.g.d_parser.cc lts_xrules.cc conf.cc end_condition.cc date.g.d_parser.cc test_engine.cc adapter.cc history.cc heuristic.cc policy.cc alg_bdfs.cc conf.g.d_parser.cc uconf.g.d_parser.cc mrules.g.d_parser.cc of.cc of_null.cc awrapper.cc null.cc aal.cc history_log.cc $(LOCAL_COVERAGES) lts_remote.cc coverage_of.cc of_html.cc of_csv.cc endhook.cc $(LOCAL_MODELS) coverage_notice.cc coverage_report_filter.cc random.cc random_c.cc function.cc params.cc remote.cc learn_proxy.cc learning.cc learn_action.cc learn_time.cc learn_function.cc readline_wrapper.cc function_const.cc function_array.cc

fmbt_droid_SOURCES            = $(COMMON_SOURCES)

fmbt_aalc_SOURCES = lang.g.d_parser.cc lang.cc helper.cc aalang_cpp.cc aalang_py.cc aalang_py3.cc aalang_java.cc params.cc

remote_adapter_loader_SOURCES = remote_adapter_loader.cc adapter.cc log.cc adapter_dummy.cc adapter_model.cc adapter_v4l2.cc helper.cc model.cc random.cc function.cc random_c.cc params.cc function_const.cc function_array.cc

fmbt_aalp_SOURCES = aalp.ll helper.cc params.cc log.cc

remote_aal_loader_SOURCES = remote_aal_loader.ll log.cc helper.cc adapter.cc awrapper.cc adapter_dummy.cc adapter_lib.cc $(LOCAL_MODELS) aal_loader.cc aal.cc params.cc verdict.cc adapter_dlopen.cc aal_java.cc aal_remote.cc remote.cc

fmbt_log2lsts_SOURCES = log2lsts.cc lts.cc model.cc log.cc coverage.cc lts.g.d_parser.cc history.cc helper.cc history_log.cc model_yes.cc params.cc adapter.cc
