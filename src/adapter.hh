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
#include "writable.hh"
#include "helper.hh"
#include "factory.hh"
#include "log.hh"

/* Creating and initialising an adapter is a call sequence

   1. constructor(log, params) where params contain configuration
   arguments

   2. set_actions(actions), by default just stored to the "actions"
   member.

   3. init()

   If init() returns true, adapter must be ready for responding to
   execute() and readAction(). If init returns false, stringify() may
   return reason for failure.
*/

class Adapter: public Writable {
public:
  Adapter(Log& l, std::string params = "");
  virtual void set_actions(std::vector<std::string>* _actions);
  virtual bool init();

  virtual void execute(std::vector<int> &action) =0;
  virtual bool readAction(std::vector<int> &action, bool block=false)=0;

  virtual Adapter* up();
  virtual Adapter* down(unsigned int a);
  virtual std::vector<std::string>& getAdapterNames();
  virtual std::vector<std::string>& getAllActions();
  void setparent(Adapter* a);
  const char* getUActionName(int action);

protected:
  Log& log;
  std::vector<std::string>* actions;

  std::vector<const char*> unames;
  Adapter* parent;
  std::vector<std::string> adapter_names;
};

FACTORY_DECLARATION(Adapter);

#endif
