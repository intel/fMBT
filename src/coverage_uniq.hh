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
#ifndef __coverage_uniq_hh__
#define __coverage_uniq_hh__

#include "coverage.hh"
#include "helper.hh"
#include <list>

class Coverage_uniq: public Coverage {
public:
  Coverage_uniq(Log& l, std::string params = "");
  virtual ~Coverage_uniq();
  virtual std::string stringify();

  virtual void push(){};
  virtual void pop(){};

  virtual bool execute(int action);
  virtual float getCoverage() { return 0.0; }

  virtual int fitness(int* actions,int n, float* fitness) {
    return 0;
  }
  virtual void history(int action,std::vector<int>& props,
		       Verdict::Verdict verdict);

  virtual void set_model(Model* _model);

private:
  std::vector<Coverage*> covs;
  unsigned len;
  std::list<int> v;
};

#endif
