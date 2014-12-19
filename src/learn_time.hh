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

#ifndef __learn_time_hh__
#define __learn_time_hh__

#define _ISOC99_SOURCE 1

#include "learning.hh"
#include "helper.hh"
#include "function.hh"
#include <math.h>

class Learn_time: public Learning {
public:
  Learn_time(Log&l,std::string s);
  virtual ~Learn_time() { }
  virtual void suggest(int action);
  virtual void execute(int action);
  virtual float getE(int action);
  virtual void setAlphabet(Alphabet* a) {
    Learning::setAlphabet(a);
    time_map.resize(alphabet->getActionNames().size()+1, NAN);
  }
protected:
  Function* learning_multiplier;
  struct timeval last_time;
  std::vector<double> time_map;
};

#endif
