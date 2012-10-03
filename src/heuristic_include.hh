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

#ifndef __heuristic_include_hh__
#define __heuristic_include_hh__

#include <vector>
#include <string>

#include "heuristic.hh"
#include "coverage.hh"
#include "lts.hh"
#include "heuristic_random.hh"
#include "model_filter.hh"

class Heuristic_include_base : public Heuristic {
public:
  Heuristic_include_base(Log& l, std::string params,bool invert);
  virtual ~Heuristic_include_base() {
    if (child) {
      delete child;
    }
  }
  virtual float getCoverage();
  virtual int getAction();
  virtual int getIAction();

  virtual void set_coverage(Coverage* c);
  virtual void set_model(Model* _model);

  virtual bool execute(int action) {
    mf.push();
    child->execute(action);
    mf.pop();
    return Heuristic::execute(action);
  }

private:
  bool exclude;
  Heuristic* child;
  Heuristic_random hr;
  Model_filter mf;
};

#endif
