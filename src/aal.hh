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
#ifndef __aal_hh__
#define __aal_hh__

#include "factory.hh"
#include "log.hh"
#include <vector>
#include <string>

class aal {
public:
  aal(Log&l): _log(l) {};
  virtual ~aal() {};
  virtual int adapter_execute(int action)=0;
  virtual int model_execute(int action)  =0;
  virtual int getActions(int** act)      =0;
  virtual bool reset() {
    return true;
  }
  virtual std::vector<std::string>& getActionNames() {
    return action_names;
  }
  virtual void push() {}
  virtual void pop() {}
  virtual void log(const char* format, ...);
protected:
  std::vector<int> actions;
  std::vector<std::string> action_names; /* action names.. */
  Log& _log;
};

#include "model.hh"
#include "adapter.hh"
#include "awrapper.hh"
#include "mwrapper.hh"

#ifndef  ASSERT_EQ
#define  ASSERT_EQ(x,v) \
    if (!((x)==(v))) {                                 \
        log.print("<aal type=\"ASSERT_EQ\" msg=\"failed: %d != %d\">", x, v); \
        return 0;                                      \
    }
#endif

#ifndef  ASSERT_NEQ
#define  ASSERT_NEQ(x,v) \
    if ((x)==(v)) {                                     \
        log.print("<aal type=\"ASSERT_NEQ\" msg=\"failed: %d != %d\">", x, v); \
        return 0;                                       \
    }
#endif

#endif
