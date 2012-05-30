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
#ifndef __coverage_set_hh__
#define __coverage_set_hh__

#include "coverage_exec_filter.hh"
#include "helper.hh"
#include <map>

class Coverage_set: public Coverage_exec_filter {
public:
  Coverage_set(Log&l,std::vector<std::string*>& _from,
	       std::vector<std::string*>& _to,
	       std::vector<std::string*>& _drop):
    Coverage_exec_filter(l,_from,_to,_drop), allowed_set_size(0,1),max_count(0) {}

  virtual ~Coverage_set();
  virtual std::string stringify();

  virtual void push();
  virtual void pop();

  virtual float getCoverage() { return sets.size(); }

  virtual void set_model(Model* _model);

  virtual bool execute(int action);

  void add_filter();

protected:
  virtual void on_drop();
  virtual void on_find();
  virtual void on_start();

  std::vector<std::pair<std::string*,std::pair<int,int> > > _fv;

private:
  bool filter();
  bool range(int action,std::pair<int,int>& requirement);
  std::vector<Coverage*> covs;
  unsigned len;

  // It's easier to use map than multiset.
  // current_set[action] is used to store the execution count.
  // Negative numbers are tags.
  std::map<int,int> current_set;

  // Maps action/tag to count requirement.
  std::map<int,std::pair<int, int> > set_filter;

  std::pair<int,int> allowed_set_size;
  int max_count;

  // Key is the set, value is count....
  std::map<int,bool> action_alphabet;

  std::map<std::map<int,int>,int > sets;
  std::list<std::map<std::map<int,int> ,int> > save_sets;
  std::list<std::map<int,int> > save_current;
};

#endif
