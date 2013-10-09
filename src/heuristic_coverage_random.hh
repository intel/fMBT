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

#ifndef __heuristic_coverage_random_hh__
#define __heuristic_coverage_random_hh__

#include <vector>
#include <string>

#include "heuristic.hh"
#include "coverage.hh"
#include "lts.hh"
#include <stdlib.h>
#include <time.h>

class Random;

class Heuristic_coverage_random : public Heuristic {
public:
  Heuristic_coverage_random(Log& l,const std::string& params);
  virtual ~Heuristic_coverage_random();
  virtual int getAction();
  virtual int getIAction();
  virtual void set_model(Model* _model);
  virtual void set_coverage(Coverage* c);

protected:
  Heuristic* h;
  Coverage* sub_coverage;
  float var;
  Random* r;
};

#endif
