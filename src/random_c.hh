/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
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

#ifndef __RANDOM_C_HH__
#include "random.hh"

class Random_C: public Random {
public:
  Random_C(const std::string& param);
  virtual ~Random_C() {}
  virtual unsigned long rand();
  //virtual double rand48();
  virtual std::string stringify();
  bool global;
  unsigned int seed;
  unsigned int initial_seed;
};


#endif /* __RANDOM_C_HH__ */
