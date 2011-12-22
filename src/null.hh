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
#ifndef __null_hh__
#define __null_hh__

#include "model.hh"
#include "log.hh"

class Null: public Model {
public:
  Null(Log&l, std::string params = ""): Model(l,params) {}
  virtual int getActions(int** actions) { return 0;}
  virtual int getIActions(int** actions) { return 0;}
  virtual bool reset() { return false;}
  virtual int getprops(int** props) { return 0;}
  virtual int  execute(int action) { return 0;}
  virtual void push() {}
  virtual void pop() {}

  virtual bool load(std::string& name) { return false; }

  virtual void add_prop(std::string* name,std::vector<int>& pr)
  {}

};

#endif
