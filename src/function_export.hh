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

#ifndef __FUNCTION_export_HH__
#define _FUNCTION_INTERNAL_
#include "function.hh"

#include <vector>

class _Function_export_double: public Function {
public:
  _Function_export_double(double* _d): d(_d) {}
  virtual ~_Function_export_double() {
  }
  virtual signed long val() {
    return *d;
  }
  virtual double fval() {
    return *d;
  }
  double* d;
};

class Export_double {
public:
  Export_double(std::string _name,double* _d):name(_name),d(_d) {
    FunctionFactory::add_factory(name, creator_func, this);
  }
  
  ~Export_double() {
    FunctionFactory::remove_factory(name);
  }

  std::string name;
  double* d;

  static Function* creator_func(std::string params,void* p) {
    double* d=(double*)p;
    return new _Function_export_double(d);
  }
};

class _Function_export_int: public Function {
public: 
  _Function_export_int(int* _d): d(_d) {}
  virtual ~_Function_export_int() {
  }
  virtual signed long val() {
    return *d;
  }
  virtual double fval() {
    return *d;
  }
  int* d;

};

class Export_int {
public:
  Export_int(std::string _name,int* _d):name(_name),d(_d) {
    FunctionFactory::add_factory(name, creator_func, this);
  }
  
  ~Export_int() {
    FunctionFactory::remove_factory(name);
  }

  std::string name;
  int* d;

  static Function* creator_func(std::string params,void* p) {
    int* d=(int*)p;
    return new _Function_export_int(d);
  }
};

#endif /* __FUNCTION_export_HH__ */
