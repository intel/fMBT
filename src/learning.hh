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

#ifndef __learning_hh__
#define __learning_hh__

#include "writable.hh"
#include "factory.hh"
#include <math.h>
#include "alphabet.hh" // To have clue about time, names...

class Log;

class Learning: public Writable {
public:
  Learning(Log&l);
  virtual ~Learning();
  virtual void setAlphabet(Alphabet* a) {
    alphabet=a;
  }
  virtual void suggest(int action) { }
  virtual void execute(int action) { }
  virtual float getF(int action)   { return 0.0; }
  virtual float getC(int sug,int exe) { return 0.0; }
  virtual float getE(int action) { return 0.0; }
protected:
  bool suggested;
  int  suggested_action;
  Alphabet* alphabet;
  Log& log;
};

FACTORY_DECLARATION(Learning)

Learning* new_learning(Log&, std::string&);

#endif
