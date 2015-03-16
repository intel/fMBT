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

#ifndef __FUNCTION_cast_HH__
#include "function.hh"

#include <vector>

class Function_int: public Function {
public:
  Function_int(const std::string& param);
  virtual ~Function_int() {
    if (child) {
      delete child;
      child=NULL;
    }
  }
  virtual signed long val() {
    return child->val();
  }
  virtual double fval() {
    return child->val();
  }
  Function* child;
};

class Function_float: public Function {
public:
  Function_float(const std::string& param);
  virtual ~Function_float() {
    if (child) {
      delete child;
      child=NULL;
    }
  }
  virtual signed long val() {
    return child->fval();
  }
  virtual double fval() {
    return child->fval();
  }
  Function* child;
};

#endif /* __FUNCTION_cast_HH__ */
