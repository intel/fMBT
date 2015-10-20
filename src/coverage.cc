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
#include "coverage.hh"
#include "helper.hh"
#include <math.h>

FACTORY_CREATORS(Coverage)
FACTORY_ADD_FACTORY(Coverage)

Coverage* CoverageFactory::create(Log& log, std::string name,
				  std::string params="")
{
  if (!creators) return NULL;

  std::map<std::string, std::pair<creator,void*> >::iterator i = (*creators).find(name);

  if (i!=(*creators).end()) {
    return (i->second.first)(log, params,i->second.second);
  } else {
    char* endp;
    float val=strtof(name.c_str(),&endp);
    if (*endp==0 && (val>=0.0 || std::isnan(val))) {
      i=(*creators).find("const");
      if (i!=(*creators).end()) {
	return (i->second.first)(log,name,i->second.second);
      }
    }
  }

  return NULL;
}


Coverage::Coverage(Log& l) :
  model(NULL), current_instance(0),log(l)
{
  log.ref();
  on_report=false;
}

Coverage::~Coverage()
{
  log.unref();
}

void Coverage::set_model(Model* _model)
{
  model=_model;
}

std::string Coverage::stringify() {
  if (!status) {
    return Writable::stringify();
  }
  return std::string("");
}

Coverage* new_coverage(Log& l,const std::string& s) {
  Coverage* ret;

  std::string name,option;
  param_cut(s,name,option);
  ret=CoverageFactory::create(l, name, option);

  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret=CoverageFactory::create(l, name, option);

  if (ret) {
    fprintf(stderr,"DEPRECATED COVERAGE SYNTAX. %s\nNew syntax is %s(%s)\n",
	    s.c_str(),name.c_str(),option.c_str());
  }
  return ret;
}
