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
#ifndef __aalang_cpp_hh__
#define __aalang_cpp_hh__


#include "aalang.hh"
#include <string>
#include <vector>
#include <list>

class aalang_cpp: public aalang {
public:
  aalang_cpp();
  virtual void set_name(std::string* _name);
  virtual void set_namestr(std::string* name);
  virtual void set_tagname(std::string* name);
  virtual void next_tag();
  virtual void set_variables(std::string* var);
  virtual void set_istate(std::string* ist);
  virtual void set_guard(std::string* gua);

  virtual void set_push(std::string* p);
  virtual void set_pop(std::string* p);

  virtual void set_body(std::string* bod);
  virtual void set_adapter(std::string* ada);
  virtual void next_action();
  virtual std::string stringify();
  virtual void set_starter(std::string* st);
private:
  void factory_register();

protected:
  std::list<std::vector<std::string> > aname;
  std::list<std::vector<std::string> > tname;
  //std::vector<std::string> aname;
  std::string s;
  int action_cnt;
  int tag_cnt;
  int name_cnt;
  std::string* istate;
  std::string* name;
  std::string push;
  std::string pop;
  bool tag;
};

#endif
