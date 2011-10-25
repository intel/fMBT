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
  Conf(Log& l,bool debug_enabled=false)
    :log(l),
     heuristic_name("random"), coverage_name("tree"),
     adapter_name("dummy"), engine_cov(1.0),
     engine_count(-1) {
    log.push("fmbt_log");
    log.set_debug(debug_enabled);
  }
  ~Conf() {
    log.pop();
  }

  void set_model(std::string&s) {
    model_name=s;
  }
  void set_heuristic(std::string&s) {
    heuristic_name=s;
  }
  void set_coverage(std::string&s) {
    split(s,coverage_name,coverage_param);
  }
  void set_adapter(std::string&s) {
    split(s,adapter_name,adapter_param);
  }
  void set_engine_cov(float f) {
    engine_cov=f;
  }
  void set_engine_count(int i) {
    engine_count=i;
  }

  void execute(bool interactive=false);

  void load(std::string& name);

  static void split(std::string& val,std::string& name,
		    std::string& param);
  
  Log& log;

  virtual std::string stringify();

 protected:
  std::string model_name;
  std::string heuristic_name;

  std::string coverage_name;
  std::string coverage_param;

  std::string adapter_name;
  std::string adapter_param;

  float engine_cov;
  int engine_count;

  Heuristic* heuristic;
  Model* model;
  Adapter* adapter;
};

#endif
