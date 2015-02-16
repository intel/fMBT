/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011,2012 Intel Corporation.
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

/* Coverage_Prop measures coverag of state propositions.
 * Coverage is 1, if all of the state propositions are set
 * at the current state.
 */

#ifndef __coverage_prop_hh__
#define __coverage_prop_hh__

#include <stack>

#include "coverage.hh"

#include <map>
#include <vector>
#include <bitset>
#include <cstdlib>
#include <list>

class Model;

class Coverage_Prop: public Coverage {

public:
  class unit;
  Coverage_Prop(Log& l, std::string& params);
  virtual ~Coverage_Prop() {}
  virtual void push();
  virtual void pop();

  virtual void history(int action, std::vector<int>& props,
		       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  virtual void set_model(Model* _model);

  int props_total;
  int props_seen;
  std::vector<bool> data;
protected:
  void regexp_try(std::string&,std::vector<std::string>&);

  std::string params;
  std::map<int,bool> prop_included;
  std::list<std::pair<std::vector<bool>,int> > state_save;
};


#endif
