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
#ifndef __aalang_py_hh__
#define __aalang_py_hh__


#include "aalang.hh"
#include <string>
#include <vector>

class aalang_py: public aalang {
public:
  aalang_py(): aalang(), name(NULL), action_cnt(1), acnt("1") { default_body="\tpass"; default_guard="\treturn 1";};

  virtual void set_starter(std::string* st);
  virtual void set_name(std::string* name);
  virtual void set_namestr(std::string* name);
  virtual void set_variables(std::string* var);
  virtual void set_istate(std::string* ist);
  virtual void set_guard(std::string* gua);

  virtual void set_push(std::string* p);
  virtual void set_pop(std::string* p);

  virtual void set_body(std::string* bod);
  virtual void set_adapter(std::string* ada);
  virtual void next_action();
  virtual std::string stringify();
protected:
  std::string* name;
  int action_cnt;
  std::string acnt;
  std::string s;
  std::string push;
  std::string pop;
};

#endif
