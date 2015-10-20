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

#define _FUNCTION_INTERNAL_
#include "random.hh"
#include "function_random.hh"

Function_random::Function_random(const std::string& param) {

  if (param!="") {
    r=new_random(param);
  } else {
    r=Random::default_random();
  }
  if (!r) {
    status=false;
    errormsg="Can't create random!";
  } else {
    status=r->status;
    errormsg=r->errormsg;
  }
  prefer=FLOAT;
}

Function_random::~Function_random() {
  r->unref();
  r=NULL;
}


double Function_random::fval() {
  return r->drand48();
}

signed long Function_random::val() {
  return r->rand();
}


FACTORY_DEFAULT_CREATOR(Function, Function_random, "random")
