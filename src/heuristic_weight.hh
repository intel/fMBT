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

#ifndef __heuristic_weight_hh__
#define __heuristic_weight_hh__

#include <vector>
#include <string>

#include "heuristic.hh"
#include "coverage.hh"
#include "lts.hh"
#include <stdlib.h>
#include <time.h>

class Heuristic_weight : public Heuristic {
public:
  Heuristic_weight(Log& l, std::string params);
  virtual float getCoverage();
  virtual int getAction();
  virtual int getIAction();
  virtual void set_model(Model* _model);
  virtual void set_coverage(Coverage* c);

  void add(std::vector<std::string*> p,
	   std::vector<std::string*> a,
	   int w);

protected:
  int weight_select(int i,int* actions);
  std::map<std::pair<int,int>, float> weights;
  std::map<std::pair<int,int>, int> weight_ids;
private:
  std::string prm;
};

#endif
