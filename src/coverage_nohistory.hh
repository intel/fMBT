/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2013, Intel Corporation.
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
#ifndef __coverage_nohistory__
#define __coverage_nohistory__

#include "coverage.hh"

class Coverage_nohistory: public Coverage {
public:
  Coverage_nohistory(Log&l,const std::string& _params) :Coverage(l) {
    child=new_coverage(l,_params);
    if (!child) {
      errormsg="Can't create civerage \""+_params+"\"";
      status=false;
      return;
    }
    if (!child->status) {
      status=child->status;
      errormsg=child->errormsg;      
    }
  }

  virtual ~Coverage_nohistory() {
    if (child) {
      delete child;
    }
  }

  virtual void push(){
    child->push();
  };
  virtual void pop(){
    child->pop();
  };

  virtual bool execute(int action) {
    return child->execute(action);
  }

  virtual float getCoverage() {
    return child->getCoverage();
  }

  virtual int fitness(int* actions,int n, float* fitness) {
    return child->fitness(actions,n,fitness);
  }

  virtual void history(int action,std::vector<int>& props,
		       Verdict::Verdict verdict) {
    
  }

  virtual void set_model(Model* _model) {
    child->set_model(_model);
    status=child->status;
    errormsg=child->errormsg;
  }

private:
  Coverage* child;
};

#endif
