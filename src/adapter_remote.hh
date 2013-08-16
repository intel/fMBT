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
#include "adapter.hh"
#include <glib.h>
#include "remote.hh"

class Adapter_remote: public Adapter, public remote {
public:
  Adapter_remote(Log& l, std::string& params, bool encode=true);
  virtual ~Adapter_remote() {
    if (d_stdin) {
      g_io_channel_shutdown(d_stdin,TRUE,NULL);
    }
    if (d_stdout) {
      g_io_channel_shutdown(d_stdout,TRUE,NULL);
    }
    if (d_stderr) {
      g_io_channel_shutdown(d_stderr,TRUE,NULL);
    }
  }
  virtual bool init();

  virtual void execute(std::vector<int>& action);
  virtual int observe(std::vector<int> &action,bool block=false);

  virtual std::string stringify();
protected:

  char* read_buf;
  size_t read_buf_pos;

  /*
  FILE* d_stdin;
  FILE* d_stdout;
  FILE* d_stderr;
  */

  GIOChannel* d_stdin;
  GIOChannel* d_stdout;
  GIOChannel* d_stderr;


  std::string prm;
  bool urlencode;
};
