/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012 Intel Corporation.
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

#ifndef __coverage_include_hh__
#define __coverage_include_hh__

#include "coverage.hh"
#include "alphabet_impl.hh"
#include "model_yes.hh"

class Coverage_Include_base: public Coverage {
public:
  Coverage_Include_base(Log& l,const std::string& param,bool _exclude);

  virtual ~Coverage_Include_base() {
    if (child) {
      delete child;
    }
  }

  virtual void push() {
    if (child) {
      child->push();
    }
  }

  virtual void pop() {
    if (child) {
      child->pop();
    }
  }

  virtual bool execute(int action) {
    if (child) { // broken...
      return child->execute(action);
    }
    return true;
  }

  virtual float getCoverage() {
    if (child) {
      return child->getCoverage();
    }
    return 0.0;
  }

  virtual void set_model(Model* _model);
  virtual int fitness(int* actions,int n, float* fitness) {
    if (child) {
      return child->fitness(actions,n,fitness);
    }
    return 0;
  }

protected:
  Alphabet_impl* alpha;
  Model_yes* submodel;
  Coverage* child;
  bool exclude;
  std::vector<std::string> subs;
  std::vector<std::string> ActionNames;
  std::vector<std::string> SPNames;
};

#endif
