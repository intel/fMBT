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
#ifndef __coverage_report_hh__
#define __coverage_report_hh__

#include "coverage_exec_filter.hh"

#include <sys/time.h>
#include <stack>

class Coverage_report: public Coverage_exec_filter {
public:
  Coverage_report(Log&l,std::vector<std::string*>& _from,
		  std::vector<std::string*>& _to,
		  std::vector<std::string*>& _drop):
    Coverage_exec_filter(l,_from,_to,_drop),count(0)
  {}

  virtual std::string stringify();

  virtual void push(){ save.push(online); save.push(count); };
  virtual void pop() { count=save.top(); save.pop(); online=save.top(); save.pop(); };

  virtual float getCoverage() { return count; }

  virtual int fitness(int* actions,int n, float* fitness) {
    return 0;
  }
  virtual void set_model(Model* _model);

  std::vector<std::vector<int> > traces;
  std::vector<std::vector<struct timeval> >  step_time;
  std::vector< struct timeval >  start_time;
  std::vector< struct timeval >  duration;

private:
  virtual void on_find();

  bool prop_set(std::vector<int> p,int npro,int* props);

  std::vector<int> executed;
  std::vector<struct timeval > etime;

  int count;
  std::stack<int> save;
};

#endif
