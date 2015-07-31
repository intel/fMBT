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
#ifndef __log_aalremote_h__
#define __log_aalremote_h__

#include "log.hh"

class Log_aalremote: public Log {
public:
  virtual ~Log_aalremote() {}
protected:
  virtual void write(const char* msg,FILE* f) {
    char* _msg=escape_string(msg);
    fprintf(stdout,"fmbtmagicL%s\n",_msg);
    escape_free(_msg);
  }

  virtual void write(const char* msg) {
    char* _msg=escape_string(msg);
    fprintf(stdout,"fmbtmagicL%s\n",_msg);
    escape_free(_msg);
  }
};

#endif
