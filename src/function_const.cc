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

#include "function_const.hh"

Function_const::Function_const(const std::string& param) {
  char* endp;
  stored_val=strtol(param.c_str(),&endp,0);
  if (*endp!=0) {
    status=false;
    errormsg="incalid charasters at const ";
    errormsg+=endp;
  }
}

signed long Function_const::val() {
  return stored_val;
}

FACTORY_DEFAULT_CREATOR(Function, Function_const, "const")
