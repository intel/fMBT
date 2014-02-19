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
#include "function_ustime.hh"

Function_ustime::Function_ustime(const std::string& param) {
}

#include "helper.hh"

signed long Function_ustime::val() {
  struct timeval tv;
  gettime(&tv);
  return tv.tv_usec + tv.tv_usec*1000000;
}

double Function_ustime::fval() {
  struct timeval tv;
  gettime(&tv);
  return (1.0*tv.tv_sec) + (1.0*tv.tv_usec)/1000000.0;
}

FACTORY_DEFAULT_CREATOR(Function, Function_ustime, "ustime")
