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
  Log(FILE* f,bool de=false): refcount(0), out(f), debug_enabled(de)  { }
  Log(): refcount(0), out(stderr), debug_enabled(false)  { }
  virtual ~Log() { if (out!=stderr) { fclose(out); } }
  virtual void push(std::string&);
  virtual void push(const char*);
  virtual void pop();

  virtual void print(const char* format,...);
  virtual void debug(const char* msg,...);
  virtual void error(const char** format,...);

  virtual void write(int action,const char *name,const char *msg);

  virtual void set_debug(bool d) {
    debug_enabled=d;
  }

  virtual bool is_debug() {
    return debug_enabled;
  }

  void ref() {
    refcount++;
  }

  void unref() {
    refcount--;
    if (refcount<=0) {
      delete this;
    }
  }


protected:
  int refcount;
  virtual void write(const char* msg,FILE* f);
  virtual void write(const char* msg)
  {
    write(msg,out);
  }
  virtual void write(std::string& msg);

  virtual void vprint(const char* format,va_list ap,FILE*,bool urldecode=false);
  virtual void vuprint(const char* format,va_list ap);

  virtual void vprint(const char* format,va_list ap) {
    vprint(format,ap,out);
  }

  FILE* out;
  std::stack<std::string> element;
  bool debug_enabled;
};


#endif
