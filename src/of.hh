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

#include "writable.hh"
#include "log_null.hh"

class Model;
class History;
class Log;

#include "coverage_report.hh"

class OutputFormat: public Writable {
public:
  OutputFormat(std::string params) : Writable(),model(NULL) {}
  virtual ~OutputFormat();
  virtual void set_model(Model* m) {
    model=m;
  }
  virtual void set_model(std::string m);

  virtual void set_prefix(std::string& _prefix)
  {
    prefix=_prefix;
  }
  virtual void add_testrun(std::string& name,
			   std::string& _model);

  virtual void add_testrun(std::string& name,
			   Model* _model);

  virtual void add_uc(std::string& name,Coverage* c);
  virtual void add_uc(std::string& name,std::string& c);

  virtual std::string handle_history(Log&l,std::string& h);

  virtual std::string header() { return "";}
  virtual std::string footer() { return "";}

  virtual void add_report(std::string& name,
			  std::vector<std::string*>& from,
			  std::vector<std::string*>& to,
			  std::vector<std::string*>& drop);

  virtual std::string report()=0;

protected:
  Model* model;
  std::string prefix;
  std::vector<Coverage*>   covs;
  std::vector<std::string> covnames;

  std::vector<Coverage_report*>   rcovs;
  std::vector<std::string>        reportnames;

  std::vector<Model*>      testruns;
  std::vector<std::string> testnames;
  Log_null l;
  virtual std::string format_covs()=0;
  

  std::string drop_tag;
  std::string completed_tag;
  std::string test_verdict;
};

#undef  FACTORY_CREATE_PARAMS
#undef  FACTORY_CREATOR_PARAMS
#undef  FACTORY_CREATOR_PARAMS2

#define FACTORY_CREATE_PARAMS std::string name, std::string params
#define FACTORY_CREATOR_PARAMS std::string params
#define FACTORY_CREATOR_PARAMS2 params

#include "factory.hh"

FACTORY_DECLARATION(OutputFormat)

#endif

