/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */
#ifndef __conf_h__
#define __conf_h__

#include <sys/time.h>
#include <string>
#include "log.hh"
#include "model.hh"
#include "test_engine.hh"
#include "heuristic.hh"
#include "adapter.hh"
#include "coverage.hh"

#include "writable.hh"
#include "helper.hh"

class EndHook;
class EndHookInteractive;
class Conf;
EndHook* new_endhook(Conf* c,const std::string& s);

class Conf:public Writable {
 public:
  friend class EndHookInteractive;
  Conf(Log& l, bool debug_enabled=false);

  virtual ~Conf();

  void disable_tagchecking(std::string&);

  void disable_tagchecking() {
    disable_tagverify=true;
  }

  void set_model(Coverage* c);

  void set_model(std::string& s,int line) {
    //split(s, model_name, model_param);
    //param_cut(s, model_name, model_param);
    model_lineno=line;
    model_name=s;
  }
  void set_heuristic(std::string& s,int line) {
    heuristic_name=s;
    heuristic_lineno=line;
    //split(s, heuristic_name, heuristic_param);
    //param_cut(s, heuristic_name, heuristic_param);
  }
  void set_coverage(std::string& s,int line) {
    //split(s, coverage_name, coverage_param);
    //param_cut(s,coverage_name,coverage_param);
    coverage_name=s;
    coverage_lineno=line;
  }
  void set_adapter(std::string& s,int line) {
    //split(s, adapter_name, adapter_param);
    //param_cut(s, adapter_name, adapter_param);
    adapter_name=s;
    adapter_lineno=line;
  }
  void set_on_error(const std::string &s,int line=-1);
  void set_on_fail(const std::string &s,int line=-1);
  void set_on_pass(const std::string &s,int line=-1);
  void set_on_inconc(const std::string &s,int line=-1);

  void add_end_condition(End_condition *ec) {
    if (ec->status) {
      end_conditions.push_back(ec);
    } else {
      status=false;
      errormsg=ec->errormsg;
    }
  }

  void add_end_condition(Verdict::Verdict v,std::string& s,int line);

  void set_observe_sleep(std::string &s);

  void add_history(std::string* s,int line) {
    history.push_back(std::pair<std::string*,int>(s,line));
  }

  Verdict::Verdict execute(bool interactive=false);

  void load(std::string& name) {
    std::string content("");
    load(name,content);
  }
  void load(std::string& name,std::string& content);
  
  Log& log;

  virtual std::string stringify();

  void handle_hooks(Verdict::Verdict v);

  int exit_status;
  bool exit_interactive;
 protected:
  std::list<EndHook*> pass_hooks,fail_hooks,inc_hooks,error_hooks;
  std::vector<std::pair<std::string*,int> > history;
  std::string model_name;
  std::string heuristic_name;
  std::string coverage_name;
  std::string adapter_name;

  int model_lineno;
  int heuristic_lineno;
  int coverage_lineno;
  int adapter_lineno;

  std::vector<End_condition*> end_conditions;

  time_t end_time;

  std::string on_error, on_fail, on_pass, on_inconc;

  Heuristic* heuristic;
  Model* model;
  Adapter* adapter;
  Coverage* coverage;
  bool disable_tagverify;
  std::map<int,bool> disabled_tags;
  std::vector<std::string> disable_tags;
  std::vector<Coverage*> set_model_callbacks;
};

#endif
