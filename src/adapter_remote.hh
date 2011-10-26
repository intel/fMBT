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

class Adapter_remote: public Adapter {
public:
  Adapter_remote(std::vector<std::string>& _actions, std::string& params,Log&l,bool encode=true);
  ~Adapter_remote() {

  }

  virtual void execute(std::vector<int>& action);
  virtual bool readAction(std::vector<int> &action,bool block=false);
  virtual std::string stringify();
  virtual bool init();
protected:
  ssize_t nonblock_getline(char **lineptr, size_t *n, FILE *stream,
                           const char delimiter = '\n');
  ssize_t agetline(char **lineptr, size_t *n, FILE *stream);

  char* read_buf;
  size_t read_buf_pos;

  FILE* d_stdin;
  FILE* d_stdout;
  FILE* d_stderr;

  std::string prm;

  std::string errormsg;
  
  GPid pid;
  bool urlencode;
};
