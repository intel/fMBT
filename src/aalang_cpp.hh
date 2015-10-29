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
#include <stack>

#include "helper.hh"

class aalang_cpp: public aalang {
public:
  aalang_cpp();
  virtual ~aalang_cpp();
  virtual void set_name(std::string* _name,bool first=false,ANAMETYPE t=DEFACTION);
  virtual void set_namestr(std::string* name);
  virtual void set_tagname(std::string* name,bool first=false);
  virtual void next_tag();
  virtual void set_variables(std::string* var,const char*,int,int);
  virtual void set_istate(std::string* ist,const char*,int,int);
  virtual void set_ainit(std::string* iai,const char*,int,int);
  virtual void set_aexit(std::string* iai,const char*,int,int);
  virtual void set_guard(std::string* gua,const char*,int,int);

  virtual void parallel(bool start);
  virtual void serial(bool start);

  virtual void set_push(std::string* p,const char*,int,int);
  virtual void set_pop(std::string* p,const char*,int,int);

  virtual void set_body(std::string* bod,const char*,int,int);
  virtual void set_adapter(std::string* ada,const char*,int,int);
  virtual void next_action();
  virtual std::string stringify();
  virtual void set_starter(std::string* st,const char*,int,int);
private:
  void factory_register();

protected:
  std::vector<std::string> anames;
  std::vector<std::string> tnames;
  std::list<std::vector<std::string> > aname;
  std::list<std::vector<std::string> > tname;
  std::list<std::string> guard_call_construct;
  std::vector<std::string> tag_guard_call;
  std::vector<std::string> action_guard_call;
  std::string s;
  int action_cnt;
  int tag_cnt;
  int name_cnt;
  std::string* istate;
  std::string* ainit;
  std::string* aexit;
  std::string* name;
  std::string push;
  std::string pop;
  bool tag;
  std::map<bool,int> tag_adapter;
  std::list<bool> tstack;
  std::list<int> name_cnt_stack;
  
  std::stack<int> outter_stack;
  int outters;
  int current_outter;

  std::stack<int> inner_stack;
  int current_inner;

  std::vector<std::list<std::string> > inner_names;
};

#endif
