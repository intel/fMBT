/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "learn_function.hh"
#include "helper.hh"
#include "adapter.hh"

Learn_time_function::Learn_time_function(Log&l,std::string&s): Learn_time(l,"") {
  f=new_function(s);
  if (!f) {
    status=false;
    errormsg="Can't create function \""+s+"\"";
  } else {
    status=f->status;
    errormsg=f->errormsg;
  }
}

float Learn_time_function::getF(int action) {
  return f->fval();
}

float Learn_time_function::getC(int sug,int exe) {
  return f->fval();
}

float Learn_time_function::getE(int action) {
  return f->fval();
}

Learn_action_function::Learn_action_function(Log&l,std::string&s): Learn_action(l,"") {
  f=new_function(s);
  if (!f) {
    status=false;
    errormsg="Can't create function \""+s+"\"";
  } else {
    status=f->status;
    errormsg=f->errormsg;
  }
}

float Learn_action_function::getF(int action) {
  return f->fval();
}

float Learn_action_function::getC(int sug,int exe) {
  return f->fval();
}

float Learn_action_function::getE(int action) {
  return f->fval();
}

FACTORY_DEFAULT_CREATOR(Learning, Learn_time_function, "time_function")
FACTORY_DEFAULT_CREATOR(Learning, Learn_action_function, "action_function")
