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
#include <list>
#include <stack>

typedef std::pair<std::string,int> fileline;
typedef std::pair<std::string,fileline> codefileline;

class aalang_py: public aalang {
public:
  aalang_py(): aalang(), name(NULL), action_cnt(1),
               tag_cnt(1), serial_cnt(1), /*acnt("1"),tcnt("1"),*/
               m_lines_in_vars(0), tag(false),
	       adapter(false) {
        default_body   ="pass";
        default_guard  ="return 1";
        default_adapter="pass";
    };

  virtual void set_starter(std::string* st,const char*,int,int);
  virtual void set_name(std::string* name,bool first=false,ANAMETYPE t=DEFACTION);
  virtual void set_namestr(std::string* name);
  virtual void set_variables(std::string* var,const char*,int,int);
  virtual void set_tagname(std::string* name,bool first=false);
  virtual void next_tag();
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
protected:
  std::string* name;
  std::vector<std::pair<std::string,int> > multiname;
  codefileline m_guard;
  codefileline m_body;
  codefileline m_adapter;
  int action_cnt;
  int tag_cnt;
  int serial_cnt;
  //std::string acnt;
  //std::string tcnt;
  std::string s;
  std::string push;
  std::string pop;
  std::string variables;
  int m_lines_in_vars;
  bool tag;
  bool adapter;
  bool this_is_input;
  std::list<std::string> guard_requires;

  std::string requires;

  std::list<bool> ta_stack;
  std::list<int> serial_stack;
  std::list<std::vector<std::pair<std::string,int > > > ma_stack;
  std::stack<codefileline> ma_save;

  const std::string class_name() const;
  std::string action_helper(const codefileline& cfl,std::string s,
			    std::string& funcname,int i,std::string& acnt);
  const std::string serialN(const std::string postfix, bool cls=false) const;
  const std::string serialN_1(const std::string postfix, bool cls=false) const;
  const int serial_stackN_1() const;
};

#endif
