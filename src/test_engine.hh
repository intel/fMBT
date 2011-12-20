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
#include "heuristic.hh"
#include "adapter.hh"
#include "log.hh"
#include "policy.hh"

#include <list>

class Test_engine {
public:
  Test_engine(Heuristic& h,Adapter& a,Log& l,Policy& p);
  bool run(float _target_coverage,int _max_step_count=-1,
	   int _exit_tag=-1);
  void interactive();
  virtual bool coverage_status(int step_count);
protected:
  int       max_step_count;
  float     target_coverage;
  int       exit_tag;
  Heuristic &heuristic;
  Adapter   &adapter;
  Log       &log;
  Policy    &policy;
  bool      coverage_reached;
  bool      step_limit_reached;
  bool      tag_reached;
};
