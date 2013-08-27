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

#ifndef __awrapper_hh__
#define __awrapper_hh__

#include <vector>
#include <string>
#include <fstream>

#include "adapter.hh"
#include "aal.hh"

#ifdef __MINGW32__
#define __MINGW_VERSION(major, minor) \
  (__MINGW32_MAJOR_VERSION > (major) \
   || (__MINGW32_MAJOR_VERSION == (major) \
   && __MINGW32_MINOR_VERSION >= (minor)))
#if __MINGW_VERSION(3,15)
#define NEEDS_MINGWHACK
#endif
#endif

class Awrapper: public Adapter {
public:
  Awrapper(Log&l, aal* _ada);
  virtual ~Awrapper();
  virtual void set_actions(std::vector<std::string>* _actions);
  virtual void set_tags(std::vector<std::string>* _tags);
  virtual bool init();
  virtual void adapter_exit(Verdict::Verdict verdict,
			    const std::string& reason);

  virtual void execute(std::vector<int>& action);
  virtual int  observe(std::vector<int> &action,bool block=false);
  virtual int check_tags(int* tag,int len,std::vector<int>& t);
protected:
  static std::string es;
#ifdef NEEDS_MINGWHACK
  std::map<std::pair<int,std::string>, int > ada2aal;
#else
  std::map<std::pair<int,std::string&>, int > ada2aal;
#endif
  std::map<int,int> aal2ada;
  std::map<int,int> tagaal2ada;
  std::map<int,int> tagada2aal;

  aal* ada;
  std::map<int,std::string> parameters;
};

#endif

