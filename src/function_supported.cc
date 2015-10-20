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
#include "function_supported.hh"
#include "params.hh"
#include "helper.hh"

Function_Supported::Function_Supported(const std::string& param) {
  std::vector<std::string> s;
  commalist(param,s);
  r=NULL;
  for(unsigned i=0;i<s.size();i++) {
    r=new_function(s[i]);
    if (r) {
      if (!r->status) {
	delete r;
	r=NULL;
      } else {
	return;
      }
    }
  }
  if (r==NULL) {
    status=false;
  }
  prefer = r->prefer;
}

Function_Supported::~Function_Supported()
{
  if (r)
    delete r;
}

std::string Function_Supported::stringify() {
  if (status) {
    return r->stringify();
  } 
  return Writable::stringify();
}

double Function_Supported::fval() {
  return r->fval();
}

signed long Function_Supported::val() {
  return r->val();
}

FACTORY_DEFAULT_CREATOR(Function, Function_Supported, "supported")
