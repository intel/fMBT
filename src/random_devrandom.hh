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

#ifndef __RANDOM_DevRandom_HH__
#include "random.hh"

class Random_Dev: public Random {
public:
  Random_Dev(const std::string& param);
  virtual ~Random_Dev();
  virtual unsigned long rand();
  virtual std::string stringify();
  int fd;
};

class Random_DevRandom: public Random_Dev {
public:
  Random_DevRandom(const std::string& param):Random_Dev("/dev/random") {}
  virtual ~Random_DevRandom() {}
};

class Random_DevuRandom: public Random_Dev {
public:
  Random_DevuRandom(const std::string& param):Random_Dev("/dev/urandom") {}
  virtual ~Random_DevuRandom() {}
};

class Random_DevRandomf: public Function {
public:
  Random_DevRandomf(const std::string& param):r(param) {
    status=r.status;
    errormsg=r.errormsg;
  }
  virtual ~Random_DevRandomf() {}
  virtual signed long val() {
    return r.rand();
  };
  virtual double fval() {
    return r.drand48();
  };
  Random_DevRandom r;
};


#endif /* __RANDOM_DevRandom_HH__ */
