/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "coverage_avoid.hh"
#include "helper.hh"
#include <cstdlib>
#include <cstring>

Coverage_avoid::~Coverage_avoid()
{
  for(unsigned i=0;i<h.size();i++) {
    delete h[i].second;
  }
}

Coverage_avoid::Coverage_avoid(Log& l, std::string& params) :
  Coverage(l)
{
  static std::string separator(":");
  char* tmp=strdup(params.c_str());
  std::string m(unescape_string(tmp));
  std::vector<std::string> s;
  strvec(s,m,separator);
  free(tmp);
  for(unsigned i=0;i+1<s.size();i+=3) {
    float f=atof(s[i].c_str());
    if (f<=0.0) {
      f=1.0;
    }
    std::string prm("");
    if (i+2<s.size()) {
      prm=s[i+2];
    }

    Coverage* cov=CoverageFactory::create(log, s[i+1], prm);
    if (cov==NULL) {
      status=false;
      errormsg=std::string("Can't create coverage ")+s[i+1];
      return;
    }
    h.push_back(std::pair<float,Coverage*>(f,cov));
  }

  if (h.empty()) {
    status=false;
    errormsg=std::string("no subcoverages?");
  }
}

float Coverage_avoid::getCoverage() {
  if (depth) {
    for(unsigned i=1;i<h.size();i++) {
      if (h[i].second->getCoverage()>=h[i].first) {
	return -1.0;
      }
    }
  }
  return h[0].second->getCoverage();
}

void Coverage_avoid::push()
{
  depth++;
  for(unsigned i=0;i<h.size();i++) {
    h[i].second->push();
  }
}

void Coverage_avoid::pop()
{
  depth--;
  for(unsigned i=0;i<h.size();i++) {
    h[i].second->pop();
  }
}

bool Coverage_avoid::execute(int action)
{
  bool ret=true;
  for(unsigned i=0;i<h.size();i++) {
    ret&=h[i].second->execute(action);
  }
  return ret;
}

int Coverage_avoid::fitness(int* actions,int n, float* fitness)
{
  return h[0].second->fitness(actions,n,fitness);
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_avoid, "avoid")
