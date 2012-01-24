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
#ifndef __of_hh__
#define __of_hh__

#include <vector>
#include <string>
#include <map>

#define FACTORY_CREATE_PARAMS std::string name, std::string params
#define FACTORY_CREATOR_PARAMS std::string params
#define FACTORY_CREATOR_PARAMS2 params

#include "writable.hh"
#include "factory.hh"
#include "alphabet.hh"

class Coverage;

class OutputFormat: public Writable {
public:
  OutputFormat(std::string params) : Writable(),alpha(NULL) {}
  virtual ~OutputFormat();
  virtual void setalphabet(Alphabet* a) {
    alpha=a;
  }
  virtual void set_prefix(std::string& prefix) =0;
  virtual void add_testrun(std::string& name)  =0;
  virtual void add_uc(std::string& name,Coverage* c);

protected:
  Alphabet* alpha;
  std::vector<Coverage*> covs;
  std::vector<std::string> covnames;
};

FACTORY_DECLARATION(OutputFormat)

#endif

