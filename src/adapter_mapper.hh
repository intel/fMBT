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

/* Adapter mapper handles renaming and redirecting actions to multiple
 * adapters.
 */

#ifndef __adapter_mapper_hh__
#define __adapter_mapper_hh__

#include "adapter.hh"
#include "model.hh"
#include "rules.hh"
#include <map>

class Adapter_mapper : public Adapter, Rules {
public:
  Adapter_mapper(Log& log, std::string params);
  virtual bool init();

  virtual void execute(std::vector<int>& action);
  virtual bool readAction(std::vector<int> &action, bool block=false);

  bool load(std::string& name);

  virtual void add_file(unsigned index, std::string& adaptername);
  virtual void add_result_action(std::string* name);
  virtual void add_component(unsigned int index, std::string& name);

  virtual Adapter* down(unsigned int a) { 
    if (a>=adapters.size()) {
      return NULL;
    }
    return adapters[a];
  } 
  virtual std::string stringify();
protected:
  bool readActionRobin(std::vector<int> &action);
  void m1_convert(int index,std::vector<int>&action);

  typedef std::pair<int,int> adapter_action;
  int anum_create(int index,std::string& n);
  int action_number(std::string& name);

  bool is_used(int action); 
  bool is_used(adapter_action& action);

  void add_map(int index,std::string& n,int action);

  unsigned int robin;
  int l_index;
  std::string params;
  std::string l_name;
  std::string load_name;

  std::map<adapter_action,int> m1;
  std::map<int,adapter_action> m2;

  std::vector<std::vector<std::string> > adapter_anames;
  std::vector<Adapter*> adapters;

};

#endif
