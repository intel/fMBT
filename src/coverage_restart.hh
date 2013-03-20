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
#ifndef __coverage_restart_hh__
#define __coverage_restart_hh__

#include "coverage.hh"
#include "helper.hh"
#include <map>
#include <memory>
#include <list>

class Coverage_Restart: public Coverage {
public:

  Coverage_Restart(Log&l, std::string& params);

  virtual ~Coverage_Restart();
  virtual void push();
  virtual void pop();

  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness) {
    return 0;
  }

  virtual void set_model(Model* _model);

  virtual bool execute(int action);

protected:
  void new_left_right();
  std::string l,r;
  Coverage* left,*right;

  std::list<Coverage* > csave;
  std::list<int> pdsave;
  std::list<float> psave;
  float previous;
  int push_depth;
};

#endif
