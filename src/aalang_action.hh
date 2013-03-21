/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, 2013 Intel Corporation.
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
#ifndef __aalang_action_hh__
#define __aalang_action_hh__

#include "aalang.hh"
#include <string>
#include <vector>
#include <list>
#include <stack>

class aalang_action: public aalang {
public:
  aalang_action(): aalang() {
  };

  virtual void set_starter(std::string* st,const char*,int,int) {}
  virtual void set_namestr(std::string* name)                   {}
  virtual void set_name(std::string* name,bool first=false,ANAMETYPE t=DEFACTION)     {
    s=s+*name + "\n";
  }
  virtual void set_variables(std::string* var,const char*,int,int) {}
  virtual void set_tagname(std::string* name,bool first=false)  {}

  virtual void next_tag()                                       {}
  virtual void set_istate(std::string* ist,const char*,int,int) {}
  virtual void set_ainit(std::string* iai,const char*,int,int)  {}
  virtual void set_guard(std::string* gua,const char*,int,int)  {}

  virtual void set_push(std::string* p,const char*,int,int)     {}
  virtual void set_pop(std::string* p,const char*,int,int)      {}

  virtual void set_body(std::string* bod,const char*,int,int)   {}
  virtual void set_adapter(std::string* ada,const char*,int,int){}
  virtual void next_action()                                    {}
  virtual std::string stringify() {
    return s;
  }
protected:
  std::string s;
};

#endif
