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
#ifndef __coverage_trace_hh__
#define __coverage_trace_hh__

#include "coverage_exec_filter.hh"
#include "helper.hh"
#include <map>

class Coverage_trace: public Coverage {
public:
  Coverage_trace(Log&l,const std::string& _params);

  virtual ~Coverage_trace();
  virtual void push();
  virtual void pop();

  virtual bool execute(int action);
  virtual float getCoverage();

  virtual std::string stringify() { return std::string(""); }

  virtual int fitness(int* actions,int n, float* fitness);
  virtual void set_model(Model* _model);

protected:
  std::string params;
  std::vector<int> act;
  unsigned pos;
  std::stack<int> st;
  std::vector<std::pair<float,Coverage*> > h;
private:

};

#endif
