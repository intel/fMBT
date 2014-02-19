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
#include "function_const.hh"

Function_const::Function_const(const std::string& param) {
  char* endp;
  if (param=="") {
    errormsg="empthy constant?";
    status=false;
    return;
  }
  stored_val=strtol(param.c_str(),&endp,0);
  if (*endp!=0) {
    stored_fval=strtod(param.c_str(),&endp);
    if (*endp!=0) {
      status=false;
      errormsg="incalid charasters at const ";
      errormsg+=endp;      
    } else {
      stored_val=stored_fval;
    }
  } else {
    stored_fval=stored_val;
  }
}

signed long Function_const::val() {
  return stored_val;
}

double Function_const::fval() {
  return stored_fval;
}

FACTORY_DEFAULT_CREATOR(Function, Function_const, "const")
