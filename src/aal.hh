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
  aal(Log&l): _log(l) {ok=true;};
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
  virtual std::vector<std::string>& getSPNames() {
    return tag_names;
  }
  virtual void push() {}
  virtual void pop() {}
  virtual int getprops(int** props) {
    return 0;
  }

  virtual int  observe(std::vector<int> &action,bool block=false) {
    return 0;
  }

  virtual void log(const char* format, ...);
  bool ok;
protected:
  std::vector<int> actions;
  std::vector<int> tags;
  std::vector<std::string> action_names; /* action names.. */
  std::vector<std::string> tag_names; /* tag/state proposition names.. */
  Log& _log;
};

#include "model.hh"
#include "adapter.hh"
#include "awrapper.hh"
#include "mwrapper.hh"

#ifndef  ASSERT_EQ
#define  ASSERT_EQ(x,v) \
    if (!((x)==(v))) {                                 \
        _log.print("<aal type=\"ASSERT_EQ\" msg=\"failed: %d == %d\">\n", x, v); \
        return 0;                                      \
    }
#endif

#ifndef  ASSERT_NEQ
#define  ASSERT_NEQ(x,v) \
    if ((x)==(v)) {                                     \
        _log.print("<aal type=\"ASSERT_NEQ\" msg=\"failed: %d != %d\">\n", x, v); \
        return 0;                                       \
    }
#endif

#endif
