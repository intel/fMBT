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
#ifndef __log_h__
#define __log_h__

#include <string>
#include <stack>
#include <stdarg.h>
#include <stdio.h>

class Log {
public:
  Log(FILE* f,bool de=false): out(f), debug_enabled(de)  { }
  Log(): out(stderr), debug_enabled(false)  { }
  virtual ~Log() {}
  virtual void push(std::string&);
  virtual void push(const char*);
  virtual void pop();

  virtual void vprint(const char* format,va_list ap);
  virtual void vuprint(const char* format,va_list ap);
  virtual void print(const char* format,...);
  virtual void debug(const char* msg,...);

  virtual void write(int action,const char *name,const char *msg);

  virtual void set_debug(bool d) {
    debug_enabled=d;
  }
protected:
  virtual void write(const char* msg);
  virtual void write(std::string& msg);

  std::stack<std::string> element;
  FILE* out;
  bool debug_enabled;
};


#endif
