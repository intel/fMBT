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
#ifndef __coverage_random_hh__
#define __coverage_random_hh__

#include "coverage.hh"
#include "helper.hh"
#include <stack>

class Random;

class Coverage_random: public Coverage {
public:
  Coverage_random(Log&l,Coverage* _parent,float _var,Random* _r): Coverage(l),parent(_parent),var(_var), r(_r) { }

  virtual ~Coverage_random() {
    if (parent)
      delete parent;
  }

  virtual void push() { 
    parent->push();
    if (!parent->status) {
      status=false;
      errormsg=parent->errormsg;
    } 
  }
  virtual void pop() {
    parent->pop();
    if (!parent->status) {
      status=false;
      errormsg=parent->errormsg;
    }
  }

  virtual int fitness(int* actions,int n, float* fitness) {
    return parent->fitness(actions,n,fitness);
  }

  virtual float getCoverage();

  virtual void set_model(Model* _model) {
    if (status) {
      Coverage::set_model(_model);
      parent->set_model(model);
      if (!parent->status) {
	status=parent->status;
	errormsg=parent->errormsg;
      }
    }
  }

  virtual bool execute(int action) {
    bool ret=parent->execute(action);
    if (!parent->status) {
      status=false;
      errormsg=parent->errormsg;
    }
    return ret;
  }


protected:
  Coverage* parent;
  float var;
  Random* r;
};

#endif
