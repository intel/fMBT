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
#include "params.hh"
#include "function.hh"

FACTORY_IMPLEMENTATION(Function)

Function* new_function(const std::string& s) {
  std::string name,option;
  param_cut(s,name,option);
  Function* ret=FunctionFactory::create(name, option);

  if (ret) {
    return ret;
  }

  // Let's try a const one.
  char* endp;
  strtod(s.c_str(),&endp);

  if (*endp==0) {
    ret=FunctionFactory::create("const", option);
  }

  return ret;
}
