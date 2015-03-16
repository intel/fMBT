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

#include "function_cast.hh"

Function_int::Function_int(const std::string& param) {
  prefer = INT;
  child=new_function(param);
  if (!child) {
    status=false;
    errormsg="Can't create \""+param+"\"";
  } else {
    status=child->status;
    errormsg=child->errormsg;
  }
}

Function_float::Function_float(const std::string& param) {
  prefer = FLOAT;
  child=new_function(param);
  if (!child) {
    status=false;
    errormsg="Can't create \""+param+"\"";
  } else {
    status=child->status;
    errormsg=child->errormsg;
  }
}

FACTORY_DEFAULT_CREATOR(Function, Function_int, "int")
FACTORY_DEFAULT_CREATOR(Function, Function_float, "float")
