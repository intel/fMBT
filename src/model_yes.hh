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
#include "model.hh"

class Model_yes: public Model {
public:
  Model_yes(Log& l,const std::string& params) :
    Model(l, params), model(NULL) {
  }

  virtual ~Model_yes() {
    /*
    if (model) {
      delete model;
    }
    */
    model=NULL;
  }

  virtual int getActions(int** _act) {
    *_act=&act[0];
    return act.size();
  }

  virtual int getIActions(int** _act) {
    *_act=&iact[0];
    return iact.size();
  }

  virtual int execute(int action) {
    return action;
  }

  virtual int getprops(int** pro) {
    *pro=&props[0];
    return props.size();
  }

  virtual bool reset() {
    return true;
  }

  virtual void push() {};
  virtual void pop() {};

  virtual bool init() { return true; };

  void set_model(Alphabet* m);
  void set_props(std::string p);
  void set_props(int* p,int c);

protected:
  std::vector<int> act;
  std::vector<int> iact;
  std::vector<int> props;

  Alphabet* model;
};
