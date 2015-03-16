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
#include "function_array.hh"
#include "helper.hh"

Function_array::Function_array(std::vector<Function*> _array,Function* _index): 
  array(_array),index(_index)
{

}


Function_array::Function_array(const std::string& param):index(NULL),float_index(false),modulo(false) {
  std::vector<std::string> params;
  commalist(param,params);
  if (params.size()<2) {
    errormsg="Not enough parameters. Need at least 2, got "+to_string((unsigned)params.size());
    status=false;
    return;
  }
  for(int i=0;i<(signed)(params.size()-1);i++) {
    Function* f=new_function(params[i]);
    if (!f) {
      status=false;
      errormsg="Can't create function \""+params[i]+"\"";
      return;
    }
    if (!f->status) {
      status=false;
      errormsg=f->errormsg;
    }
    array.push_back(f);
  }
  index = new_function(params.back());
  
  if (!index) {
    status=false;
    errormsg="Can't create function \""+params.back()+"\"";
    return;
  }

  if (!index->status) {
    status=false;
    errormsg=index->errormsg;
  }

  if (index->prefer==FLOAT) {
    float_index=true;
  }

}

int Function_array::ind() {
  int pos;

  if (float_index) {
    pos = index->fval()*(array.size()-1);
  } else {
    pos=index->val();
  }
    
  if (modulo) {
    if (pos<0) {
      pos=-pos;
    }
    return pos%array.size();
  }

  if (pos<0) {
    pos=0;
  }
  
  if ((unsigned)pos>=array.size()) {
    pos=array.size()-1;
  }
  return pos;
}

signed long Function_array::val() {
  return array[ind()]->val();
}

double Function_array::fval() {
  return array[ind()]->fval();  
}

FACTORY_DEFAULT_CREATOR(Function, Function_array, "array")
