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

#include <string>
#include "log.hh"
#include "model.hh"
#include "test_engine.hh"
#include "heuristic.hh"
#include "adapter.hh"
#include "coverage.hh"

#include "writable.hh"

class Conf:public Writable {
 public:
  Conf(Log& l, bool debug_enabled=false)
    :log(l),
     heuristic_name("random"), coverage_name("perm"),
     adapter_name("dummy"), engine_cov(1.0),
     engine_count(-1), on_error("interactive")
  {
    log.push("fmbt_log");
    log.set_debug(debug_enabled);
  }
  ~Conf() {
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
  void set_engine_cov(float f) {
    engine_cov = f;
  }
  void set_engine_count(int i) {
    engine_count = i;
  }
  void set_engine_tag(std::string &s) {
    exit_tag=s;
  }
  void set_on_error(std::string &s) {
    on_error = s;
  }
  void add_history(std::string* s) {
    history.push_back(s);
  }

  void execute(bool interactive=false);

  void load(std::string& name);

  static void split(std::string& val, std::string& name,
		    std::string& param);
  
  Log& log;

  virtual std::string stringify();


 protected:
  std::string exit_tag;
  std::vector<std::string*> history;
  std::string model_name;
  std::string model_param;

  std::string heuristic_name;
  std::string heuristic_param;

  std::string coverage_name;
  std::string coverage_param;

  std::string adapter_name;
  std::string adapter_param;

  float engine_cov;
  int engine_count;

  std::string on_error;

  Heuristic* heuristic;
  Model* model;
  Adapter* adapter;
};

#endif
