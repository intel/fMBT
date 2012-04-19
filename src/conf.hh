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

class Conf:public Writable {
 public:
  Conf(Log& l, bool debug_enabled=false)
    :log(l), exit_status(0),
     heuristic_name("random"), coverage_name("perm"),
     adapter_name("dummy"), end_time(-1),
     on_error("exit:1"), on_fail("interactive"),
     on_pass("exit:0"), on_inconc("exit:1")
  {
    log.push("fmbt_log");
    log.set_debug(debug_enabled);
  }
  virtual ~Conf() {
    for (unsigned int i = 0; i < end_conditions.size(); i++)
      delete end_conditions[i];
    log.pop();
  }

  void set_model(std::string& s) {
    split(s, model_name, model_param);
  }
  void set_heuristic(std::string& s) {
    split(s, heuristic_name, heuristic_param);
  }
  void set_coverage(std::string& s) {
    split(s, coverage_name, coverage_param);
  }
  void set_adapter(std::string& s) {
    split(s, adapter_name, adapter_param);
  }
  void set_on_error(std::string &s) {
    on_error = s;
  }
  void set_on_fail(std::string &s) {
    on_fail = s;
  }
  void set_on_pass(std::string &s) {
    on_pass = s;
  }
  void set_on_inconc(std::string &s) {
    on_inconc = s;
  }

  void add_end_condition(End_condition *ec) {
    end_conditions.push_back(ec);
  }

  void set_observe_sleep(std::string &s);

  void add_history(std::string* s) {
    history.push_back(s);
  }

  Verdict::Verdict execute(bool interactive=false);

  void load(std::string& name) {
    std::string content("");
    load(name,content);
  }
  void load(std::string& name,std::string& content);
  
  Log& log;

  virtual std::string stringify();

  int exit_status;

 protected:
  void set_exitvalue(std::string& s);
  std::vector<std::string*> history;
  std::string model_name;
  std::string model_param;

  std::string heuristic_name;
  std::string heuristic_param;

  std::string coverage_name;
  std::string coverage_param;

  std::string adapter_name;
  std::string adapter_param;

  std::vector<End_condition*> end_conditions;

  time_t end_time;

  std::string on_error, on_fail, on_pass, on_inconc;

  Heuristic* heuristic;
  Model* model;
  Adapter* adapter;
};

#endif
