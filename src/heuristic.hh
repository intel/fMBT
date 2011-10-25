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
#ifndef __heuristic_hh__
#define __heuristic_hh__

#include <vector>
#include <string>

#include "coverage.hh"
#include "model.hh"

class Heuristic {
public:
  typedef Heuristic*(*creator)(Log&);
  Heuristic(Log&l): log(l) {}
  static void add_factory(std::string name, creator c);
  static Heuristic* create(Log&l,std::string name);

  virtual bool execute(int action);
  std::vector<std::string>& getAllActions();

  std::string& getActionName(int action) {
    none=std::string("NONE");
    if (action>0) {
      return model->getActionName(action);
    } return none;
  }
  Model* get_model() {
    return model;
  }
  virtual float getCoverage();
  virtual int getAction()=0;
  virtual int getIAction()=0;

  void set_coverage(Coverage* c) {
    my_coverage=c;
  }

  void set_model(Model* _model) {
    model=_model;
  }

private:
  static std::map<std::string,creator>* factory;
protected:
  std::vector<Coverage*> coverage;
  Model* model;
  Coverage* my_coverage;
  std::string none;
  Log& log;
};

namespace {
  class Heuristic_Creator {
  public:
    Heuristic_Creator(std::string name, Heuristic::creator c) {
      Heuristic::add_factory(name,c);
    }
  };
};

#endif
