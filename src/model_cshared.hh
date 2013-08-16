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
#include "model.hh"

class Model_cshared: public Model {
public:
  Model_cshared(Log&l,Model* m): Model(l,""),pr(NULL),child(m) {

  }

  virtual ~Model_cshared() {}

  virtual std::vector<std::string>& getActionNames() {
    return child->getActionNames();
  }

  virtual std::vector<std::string>& getSPNames() {
    return child->getSPNames();
  }

  virtual std::string& getActionName(int action) {
    return child->getActionName(action);
  }


  virtual int getActions(int** _act) {
    return child->getActions(_act);
  }

  virtual int getIActions(int** _act) {
    return child->getIActions(_act);
  }

  virtual int execute(int action) {
    return child->execute(action);
  }

  virtual int getprops(int** props) {
    if (pr) {
      *props=pr;
      return n;
    }
    return child->getprops(props);
  }

  virtual void push() {
    child->push();
  }

  virtual void pop() {
    child->pop();
  }

  virtual bool reset() {
    return child->reset();
  }

  virtual bool init() {
    return child->init();
  }

  int*  pr;
  int   n;
  
  Model* child;
};

