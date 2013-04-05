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
#ifndef __aalang_hh__
#define __aalang_hh__

#include <string>
#include <vector>

class aalang {
public:
  enum ANAMETYPE {
    DEFACTION,
    IACT,
    OBSERVE
  };

  aalang() {}
  virtual ~aalang() {};
  virtual void set_name(std::string* name,bool first=false,ANAMETYPE t=DEFACTION) = 0;
  virtual void set_namestr(std::string* name)                      = 0;
  virtual void set_tagname(std::string* name,bool first=false)     = 0;
  virtual void next_tag()                                          = 0;
  virtual void set_variables(std::string* var,const char*,int,int) = 0;
  virtual void set_istate(std::string* ist,const char*,int,int)    = 0;
  virtual void set_ainit(std::string* iai,const char*,int,int)     = 0;
  virtual void set_aexit(std::string* iai,const char*,int,int)     = 0;
  virtual void set_guard(std::string* gua,const char*,int,int)     = 0;

  virtual void set_push(std::string* p,const char*,int,int)        = 0;
  virtual void set_pop(std::string* p,const char*,int,int)         = 0;

  virtual void empty_guard() {
    set_guard(&default_guard,"default",0,0);
  }
  virtual void set_body(std::string* bod,const char*, int, int) = 0;
  virtual void empty_body() {
    set_body(&default_body,"default",0,0);
  }
  virtual void set_adapter(std::string* ada,const char*,int,int) = 0;
  virtual void empty_adapter() {
    set_adapter(&default_adapter,"default",0,0);
  }
  virtual void next_action() = 0;
  virtual std::string stringify() = 0;
  virtual void set_starter(std::string* st,const char*, int, int) = 0;
protected:
  std::string default_guard;
  std::string default_body;
  std::string default_adapter;
  std::vector<int> amap;
  std::vector<int> tmap;
};

#endif
