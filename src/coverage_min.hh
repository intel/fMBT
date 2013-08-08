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

/* Coverage_Min measures coverag of state minositions.
 * Coverage is 1, if all of the state minositions are set
 * at the current state.
 */

#ifndef __coverage_min_hh__
#define __coverage_min_hh__

#include <stack>

#include "coverage.hh"

#include <map>
#include <vector>
#include <bitset>
#include <cstdlib>
#include <list>

class Model;

class Coverage_Min: public Coverage {
public:
  class unit {
  public:
    virtual ~unit() {}
    virtual void next(float, bool) =0;
    virtual float value() =0;
  };

  class unit_min: public unit {
  public:
    virtual ~unit_min() {}
    virtual void next(float f,bool first) {
      if (first) {
	v=f;
      } else {
	if (v>f) {
	  v=f;
	}
      }
    }
    virtual float value() {
      return v;
    }
    float v;
  };

  class unit_max: public unit {
  public:
    virtual ~unit_max() {}
    virtual void next(float f,bool first) {
      if (first) {
	v=f;
      } else {
	if (v<f) {
	  v=f;
	}
      }
    }
    virtual float value() {
      return v;
    }
    float v;
  };

  class unit_sum: public unit {
  public:
    virtual ~unit_sum() {}
    virtual void next(float f,bool first) {
      if (first) {
	v=f;
      } else {
	v+=f;
      }
    }
    virtual float value() {
      return v;
    }
    float v;
  };

  Coverage_Min(Log& l, std::string& params,unit* _u);
  virtual ~Coverage_Min() {
    delete u;
    for(unsigned i=0;i<coverages.size();i++) {
      delete coverages[i];
    }
  }
  virtual void push();
  virtual void pop();

  virtual void history(int action, std::vector<int>& mins,
		       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  virtual void set_model(Model* _model);

  virtual bool set_instance(int instance) {
    for(unsigned i=0;i<coverages.size();i++) {
      if (!coverages[i]->set_instance(instance)) {
	for(unsigned j=0;j<i;j++) {
	  coverages[i]->set_instance(0);
	  return false;
	}
      }
    }
    return true;
  }

protected:
  std::string params;
  std::vector<Coverage*> coverages;
  unit* u;
};


#endif
