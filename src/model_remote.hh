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
#include "model.hh"
#include <glib.h>

class Model_remote: public Model {
public:
  Model_remote(Log& l, std::string& params) :
    Model(l, params), prm(params) {
  }
  virtual ~Model_remote() {
  }

  virtual int getActions(int** act);
  virtual int getIActions(int** act);

  virtual int execute(int action);
  virtual int getprops(int** pro);
  virtual bool reset();

  virtual void push();
  virtual void pop();

  virtual bool init();

protected:

  GIOChannel* d_stdin;
  GIOChannel* d_stdout;
  GIOChannel* d_stderr;

  /*
  FILE* d_stdin;
  FILE* d_stdout;
  FILE* d_stderr;
  */

  std::string prm;
  
  std::vector<int> actions;
  std::vector<int> props;
};
