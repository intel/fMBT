/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, 2012 Intel Corporation.
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

#include "config.h"
#ifndef DROID
#ifndef __aal_remote_hh__
#define __aal_remote_hh__

#include "aal.hh"
#include <glib.h>
#include "remote.hh"
#include "lts.hh"

class aal_remote: public aal, public remote {
public:
  aal_remote(Log&l,std::string&);
  virtual ~aal_remote() {
    fclose(d_stdin);
    fclose(d_stdout);
    fclose(d_stderr);
    if (lts) {
      delete lts;
    }
  };

  virtual int adapter_execute(int action,const char* params);
  virtual int model_execute(int action);
  virtual int getActions(int** act);
  virtual bool reset();
  virtual bool init();

  virtual void push();
  virtual void pop();
  virtual int getprops(int** props);

  virtual int check_tags(std::vector<int>& tag);
  virtual int observe(std::vector<int> &action,bool block=false);
private:
  void handle_stderr();

  FILE* d_stdin;
  FILE* d_stdout;
  FILE* d_stderr;

  int accel;

  Lts* lts;
};

#endif
#endif
