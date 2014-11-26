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

#ifndef __learn_action_hh__
#define __learn_action_hh__

#include "learning.hh"
#include "helper.hh"
#include "function.hh"

class Learn_action: public Learning {
public:
  Learn_action(Log&l,std::string&s);
  bool add_action(std::string& param);
  virtual ~Learn_action() { }
  virtual void setAlphabet(Alphabet* a);
  virtual void suggest(int action);
  virtual void execute(int action);
  virtual float getF(int action);
  virtual float getC(int sug,int exe);
protected:
  std::string constructor_param;
  struct as {
  public:
    as(): learning_multiplier(NULL),value(0.0) {}
    as(const struct as&_a)
    {
      learning_multiplier=_a.learning_multiplier;
      value=_a.value;
    }
    as(Function* _learn):learning_multiplier(_learn),value(1.0) {
      //learning_multiplier->ref();
    }
    ~as() {
      //if (learning_multiplier)
      //learning_multiplier->unref();
    }
    Function* learning_multiplier;
    float     value;
  };
  std::map<int,struct as> action_map;
  std::vector<std::vector<int> > pvec;
};

#endif
