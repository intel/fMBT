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

#ifndef __FUNCTION_array_HH__
#include "function.hh"

#include <vector>

class Function_array: public Function {
public:
  Function_array(const std::string& param);
  Function_array(std::vector<Function*>,Function*);
  virtual ~Function_array() {
    if (index) {
      delete index;
      index=NULL;
    }
  }
  virtual signed long val();
  virtual double fval();
  inline int ind();
  std::vector<Function*> array;
  Function* index;
  bool float_index;
  bool modulo;
};


#endif /* __FUNCTION_array_HH__ */
