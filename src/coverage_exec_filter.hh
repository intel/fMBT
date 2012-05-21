/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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
#ifndef __coverage_exec_filter_hh__
#define __coverage_exec_filter_hh__

#include "coverage.hh"
#include "helper.hh"
#include <list>

class Coverage_exec_filter: public Coverage {
public:
  // Coverage_exec_filter(Log& l,std::string params = "");
  Coverage_exec_filter(Log&l,std::vector<std::string*>& _from,
		       std::vector<std::string*>& _to,
		       std::vector<std::string*>& _drop):
    Coverage(l),from(_from),to(_to),drop(_drop),online(false) {
    printf("Coverage_exec_filter::Coverage_exec_filter()\n");
  }

  virtual ~Coverage_exec_filter() {}
  virtual std::string stringify();

  virtual void push(){
    save_online.push_front(online);
    save_executed.push_front(executed);
  };

  virtual void pop(){
    online=save_online.front();
    save_online.pop_front();

    executed=save_executed.front();
    save_executed.pop_front();
  };

  virtual bool execute(int action);
  virtual float getCoverage() { return 0.0; }

  virtual int fitness(int* actions,int n, float* fitness) { return 0; }

  virtual void set_model(Model* _model);

protected:
  bool prop_set(std::vector<int> p,int npro,int* props);

  virtual void on_drop() { };
  virtual void on_find() { };
  virtual void on_start() { };

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
  std::list<bool> save_online;
  std::list<std::vector<int> > save_executed;
};

#endif
