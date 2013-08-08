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
  Coverage(l),
  depth(0)
{
  std::vector<std::string> s;
  commalist(params,s);

  for(unsigned i=0;i+1<s.size();i+=2) {
    float f=atof(s[i].c_str());
    if (f<=0.0) {
      f=1.0;
    }

    Coverage* cov=new_coverage(log,s[i+1]);

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

bool Coverage_avoid::set_instance(int instance)
{
  for(unsigned i=0;i<h.size();i++) {
    if (!h[i].second->set_instance(instance)) {
      for(unsigned j=0;j<i;j++) {
	h[i].second->set_instance(0);
	return false;
      }
    }
  }
  return true;
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

void Coverage_avoid::set_model(Model* _model) {
  Coverage::set_model(_model);
  for(unsigned i=0;i<h.size();i++) {
    h[i].second->set_model(_model);
  }
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_avoid, "avoid")
