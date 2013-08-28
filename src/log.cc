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
#include "log.hh"
#include <cstdio>
#include <cstdlib>
#include "helper.hh"

#ifndef DROI
#include <glib.h>
#include <glib/gprintf.h>
#else
#define g_vasprintf vasprintf
#endif

void Log::push(std::string&s) {
  print("<%s>\n",s.c_str());
  element.push(s);
}

void Log::push(const char*s)
{
  std::string ss(s);
  push(ss);
}


void Log::pop() {
  std::string s = element.top();
  element.pop();
  print("</%s>\n",s.c_str());
}

#include <stdarg.h>
void Log::vprint(const char* format,va_list ap,FILE* f,bool urldecode)
{
  char* msg=NULL;

  if (g_vasprintf(&msg,format,ap)>0) {
    if (urldecode) {
      write(unescape_string(msg), f);
    } else {
      write(msg,f);
    }
    std::free(msg);
  }
  fflush(out);
}

void Log::vuprint(const char* format,va_list ap)
{
  char* msg=NULL;

  if (g_vasprintf(&msg,format,ap)>0) {
    char* m=escape_string(msg);
    write(m);
    escape_free(m);
    std::free(msg);
  }
}

void Log::print(const char* format,...)
{
  va_list ap;
  for (unsigned int i=1; i<element.size(); i++) fprintf(out, "    ");
  va_start(ap, format);
  vprint(format,ap);
  va_end(ap);
}

void Log::write(int action,const char *name,const char *msg)
{
  fprintf(out,"Action %i, name \"%s\", msg \"%s\"\n",
         action,name,msg);
}

void Log::write(const char* msg,FILE* f)
{
  fprintf(f,"%s",msg);
}

void Log::write(std::string& msg)
{
  write(msg.c_str());
}

void Log::error(const char** format,...)
{
  va_list ap0,ap1;

  for (unsigned int i=1; i<element.size(); i++) fprintf(out, "    ");

  va_start(ap0, format);
  va_start(ap1, format);
  vprint(format[0],ap0);
  vprint(format[1],ap1,stderr,true);
  va_end(ap0);
  va_end(ap1);
}

void Log::debug(const char* msg,...)
{
  if (debug_enabled) {
    va_list ap;

    va_start(ap, msg);
    write("<debug msg=\"");
    vuprint(msg,ap);
    va_end(ap);
    write("\"/>\n");
  }
}
