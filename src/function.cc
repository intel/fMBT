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
#include "function_const.hh"
#include "function_array.hh"

FACTORY_IMPLEMENTATION(Function)

Function* new_function(const std::string& s) {
  std::string name,option;
  param_cut(s,name,option);

  Function::PREFER p=Function::CARE;
  Function* ret;

  if (name=="INT") {
    p=Function::INT;
  }
  if (name=="FLOAT") {
    p=Function::FLOAT;
  }

  if (p==Function::CARE) {
    ret=FunctionFactory::create(name, option);
  } else {
    ret=new_function(option);
    if (ret) {
      ret->prefer=p;
    }
  }

  if (ret) {
    return ret;
  }

  // Do we have ':' ?

  size_t found=s.find_last_of(":");

  if (found!=std::string::npos) {
    // Let's try array..
    Function* first=new_function(s.substr(0,found));
    Function* last=new_function(s.substr(found+1));

    if (first&&last) {
      int inc=1;
      std::vector<Function*> array;
      Function* index = new Function_const(0);
      if (first->val()>last->val()) {
	inc=-1;
      }
      int i=first->val();
      for(;i!=last->val();i+=inc) {
	array.push_back(new Function_const(i));
      }
      array.push_back(new Function_const(i));
      return new Function_array(array,index);
    }
    if (first) 
      delete first;
    if (last)
      delete last;
  }

  // Let's try a const one.
  char* endp;
  (void)strtod(s.c_str(),&endp);

  if (*endp==0) {
    ret=FunctionFactory::create("const", name);
  }

  return ret;
}
