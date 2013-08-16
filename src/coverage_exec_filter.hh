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
#include <stack>
#include "log_null.hh"

class Coverage_exec_filter: public Coverage {
public:
  // Coverage_exec_filter(Log& l,std::string params = "");
  Coverage_exec_filter(Log&l,std::vector<std::string*>& _from,
		       std::vector<std::string*>& _to,
		       std::vector<std::string*>& _drop):
    Coverage(l),from(_from),to(_to),drop(_drop),online(false) {
  }

  virtual ~Coverage_exec_filter();
  virtual std::string stringify();

  virtual bool set_instance(int instance) {
    if (current_instance!=instance) {
      instance_map_efilter[current_instance]=std::pair<
	std::vector<std::pair<int,std::vector<int> > >, bool>(executed,online);
      
      std::map<int,std::pair<std::vector<std::pair<int,std::vector<int> > >,bool> >::iterator i = instance_map_efilter.find(instance);
      
      if (i == instance_map_efilter.end()) {
	online=false;
	executed.clear();
      } else {
	online = i->second.second;
	executed = i->second.first;
      }
    }

    return false;
    
  }

  virtual void push(){
    save_online.push(online);
    save_executed.push(executed);
  };

  virtual void pop(){
    online=save_online.top();
    save_online.pop();

    executed=save_executed.top();
    save_executed.pop();
  };

  virtual bool execute(int action);
  virtual float getCoverage() { return 0.0; }

  virtual int fitness(int* actions,int n, float* fitness) { return 0; }

  virtual void set_model(Model* _model);

protected:
  static void ds(std::string* s);
  bool prop_set(std::vector<int> p,int npro,int* props);

  virtual void on_drop(int action,std::vector<int>&p);
  virtual void on_find(int action,std::vector<int>&p);
  virtual void on_start(int action,std::vector<int>&p);
  virtual void on_restart(int action,std::vector<int>&p) { };
  virtual void on_online(int action,std::vector<int>&p);
  virtual void on_offline(int action,std::vector<int>&p) { };
  void mhandler(std::vector<std::string>& sp,std::vector<std::string>& n,
		std::vector<std::string*>& from,std::vector<int>& act,
		std::vector<int>& tag);
public:
  std::vector<std::pair<int,std::vector<int> > > executed;
  std::vector<struct timeval > etime;
protected:

  std::vector<int> start_tag;
  std::vector<int> end_tag;
  std::vector<int> rollback_tag;

  std::vector<int> start_action;
  std::vector<int> end_action;
  std::vector<int> rollback_action;

  std::vector<std::string*>& from;
  std::vector<std::string*>& to;
  std::vector<std::string*>& drop;
public:
  bool online;
protected:
  std::stack<bool> save_online;
  std::stack<std::vector<std::pair<int,std::vector<int> > > > save_executed;

  std::map<int,std::pair<std::vector<std::pair<int,std::vector<int> > >,bool> > instance_map_efilter;

};

#endif
