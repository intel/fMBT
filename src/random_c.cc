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
#define _RANDOM_INTERNAL_
#include "function.hh"
#include "random_c.hh"
#include <cstdlib>

Random_C::Random_C(const std::string& param) {
  max_val = RAND_MAX;
  if (param=="") {
    global=true;
    single=true;
  } else {
    Function* f=new_function(param);
    if (f==NULL) {
      status=false;
      errormsg="Can't create function "+param;
      return;
    }

    if (!f->status) {
      status=false;
      errormsg="Function error:"+f->errormsg;
      return;
    }

    seed = f->val();
    global=false;
    delete f;
  }
}

unsigned long Random_C::rand() {
  if (global) {
    return std::rand();
  }
  return rand_r(&seed);
}

FACTORY_DEFAULT_CREATOR(Random, Random_C, "C")
FACTORY_DEFAULT_CREATOR(Random, Random_C, "c")
