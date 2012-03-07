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

#include "coverage.hh"

#include <sys/time.h>

class Coverage_report: public Coverage {
public:
  Coverage_report(Log&l,std::vector<std::string*>& _from,
		  std::vector<std::string*>& _to,
		  std::vector<std::string*>& _drop):
    Coverage(l),from(_from),to(_to),drop(_drop),online(false),count(0)
  {}

  virtual std::string stringify();

  virtual void push(){};
  virtual void pop(){};

  virtual bool execute(int action);
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

  bool prop_set(std::vector<int> p,int npro,int* props);

  std::vector<int> executed;
  std::vector<struct timeval > etime;

  std::vector<int> start_tag;
  std::vector<int> end_tag;
  std::vector<int> rollback_tag;

  std::vector<int> start_action;
  std::vector<int> end_action;
  std::vector<int> rollback_action;

  std::vector<std::string*> from;
  std::vector<std::string*> to;
  std::vector<std::string*> drop;
  bool online;
  int count;
};

#endif
