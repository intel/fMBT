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
#ifndef __adapter_h__
#define __adapter_h__

#include <vector>
#include <string>
#include <map>
#include "log.hh"
#include "writable.hh"
#include "helper.hh"

class Adapter: public Writable {
public:
  typedef Adapter*(*creator)(std::vector<std::string>&,
 			     std::string,Log&);
  static void add_factory(std::string name, creator c);
  static Adapter* create(std::string name,
			 std::vector<std::string>& actions,
			 std::string params,Log&);

  Adapter(std::vector<std::string>& _actions,Log&l);

  virtual bool init() { return true;};
  virtual void execute(std::vector<int> &action) =0;
  virtual bool readAction(std::vector<int> &action,bool block=false)=0;
  /*
    virtual int execute(int action)=0;
    virtual bool readAction(int &action,bool block=false)=0;
  */
  virtual Adapter* up();
  virtual Adapter* down(unsigned int a);
  virtual std::vector<std::string>& getAdapterNames() { return adapter_names; }
  virtual std::vector<std::string>& getAllActions() { return actions; }
  void setparent(Adapter* a) { parent = a; }
  const char* getUActionName(int action) {
    if (!unames[action]) {
      unames[action]=escape_string(actions[action].c_str());
    }
    return unames[action];
  }

private:
  static std::map<std::string,creator>* factory;
protected:
  std::vector<const char*> unames;
  Adapter* parent;
  std::vector<std::string> adapter_names;
  std::vector<std::string>& actions;
  Log&log;
};

namespace {
  class adapter_factory {
  public:
    adapter_factory(std::string name, Adapter::creator c) {
      Adapter::add_factory(name,c);
    }
  };
};

#endif
