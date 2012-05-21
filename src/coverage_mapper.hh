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
#ifndef __coverage_mapper_hh__
#define __coverage_mapper_hh__

#include "coverage.hh"
#include "rules.hh"
#include <map>
#include <vector>

class Coverage_Mapper: public Coverage, Rules {
public:
  Coverage_Mapper(Log& l, std::string params = "");

  virtual std::string stringify();

  virtual void push();
  virtual void pop();

  virtual void history(int action, std::vector<int>& props,
		       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  bool load(std::string& name);

  virtual void add_file(unsigned index, std::string& adaptername);
  virtual void add_result_action(std::string* name);
  virtual void add_component(unsigned index,std::string& name,bool tau=true);

  virtual void set_model(Model* _model);
protected:
  bool pload(std::string& name);
  int l_index;
  std::string l_name;
  std::string load_name;

  std::vector<Model*> models;
  
  std::vector<Coverage*> coverages;
  typedef std::pair<int,int> coverage_action; // coverage, action
  std::multimap<int,coverage_action> m;

  void add_map(unsigned int index,std::string& n,int action);

  // name of the coverage modules to be loaded.
  std::vector<std::string> coverage_names;
  unsigned depth;
  std::vector<int> trace;
};

#endif
