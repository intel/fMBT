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

#ifndef __learn_proxy_hh__
#define __learn_proxy_hh__

#include "learn_time.hh"
#include "learn_action.hh"
#include "helper.hh"
#include "function.hh"

class Learn_proxy: public Learning {
public:
  Learn_proxy(Log&l);
  virtual ~Learn_proxy() { }
  virtual void suggest(int action);
  virtual void execute(int action);
  virtual float getE(int action);
  virtual float getF(int action);
  virtual float getC(int sug,int exe);
  virtual void setAlphabet(Alphabet* a);

  Learning*   lt;
  Learn_action* la;
};

#endif
