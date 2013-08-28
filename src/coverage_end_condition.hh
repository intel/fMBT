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
#ifndef __coverage_end_condition_hh__
#define __coverage_end_condition_hh__

#include "coverage.hh"
#include "helper.hh"
#include <stack>

class Coverage_Steps: public Coverage {
public:
  Coverage_Steps(Log&l,const std::string& params): Coverage(l),val(-1),count(0),reset_value(-1) {
    if (params!="") {
      std::vector<std::string> subs;
      commalist(params,subs);
      val=atoi(subs[0].c_str());
      if (subs.size()==2) {
        reset_value=atoi(subs[1].c_str());
      }
    }
  }

  virtual ~Coverage_Steps() { }
  virtual std::string stringify() {
    return std::string("steps(")+to_string(val)+","+to_string(reset_value)+")";
  }

  virtual void push() { save.push(count); }
  virtual void pop() { count=save.top(); save.pop(); }

  virtual float getCoverage() {

    if (val==-1) {
      return count;
    }

    if (count<val) {
      return 0.0;
    }
    return 1.0;
}

  virtual int fitness(int* actions,int n, float* fitness) {
    return 0;
  }

  virtual void set_model(Model* _model) {}

  virtual bool execute(int action) {
    count++;
    if (count==reset_value) {
      count=0;
    }
    return true;
  }


protected:
  int val;
  int count;
  int reset_value;
  std::stack<int> save;
};

#endif
