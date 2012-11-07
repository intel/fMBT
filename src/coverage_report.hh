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

  virtual ~Coverage_report() {

  }

  virtual std::string stringify();

  virtual void push();
  virtual void pop();

  virtual float getCoverage() { return count; }

  virtual int fitness(int* actions,int n, float* fitness) {

    return 0;
  }

  std::vector<std::vector<std::pair<int,std::vector<int> > > > traces;
  // std::vector<std::vector<struct timeval> >  step_time;
  // We _could_ use set instead of map, but we'll count how many instanses of the trace we have.
  std::map<std::vector<std::pair<int,std::vector<int> > >, int> tcount;
  //  std::vector< struct timeval >  start_time;
  //  std::vector< struct timeval >  duration;

protected:
  virtual void on_find(int action,std::vector<int>&p);
  virtual void on_online(int action,std::vector<int>&p);

private:
  //  bool prop_set(std::vector<int> p,int npro,int* props);

  std::vector<struct timeval > etime;
protected:
  int count;
private:
  std::stack<int> save;
  std::stack<std::vector<std::vector<std::pair<int,std::vector<int> > > > > traces_save;
  std::stack<std::map<std::vector<std::pair<int,std::vector<int> > >, int> > tcount_save;
};

#endif
