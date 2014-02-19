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

#ifndef __RANDOM_INTEL_HW_HH__
#include "function.hh"
#include "random.hh"

class Random_Intel_HW: public Random {
public:
  Random_Intel_HW(const std::string& param);
  virtual ~Random_Intel_HW() {}
  virtual unsigned long rand();
  virtual std::string stringify();
};

class Random_Intel_HWf: public Function {
public:
  Random_Intel_HWf(const std::string& param):r(param) {
    status=r.status;
    errormsg=r.errormsg;
  }
  virtual ~Random_Intel_HWf() {}
  virtual signed long val() {
    return r.rand();
  };
  virtual double fval() {
    return r.drand48();
  };
  Random_Intel_HW r;
};


#endif /* __RANDOM_INTEL_HW_HH__ */
