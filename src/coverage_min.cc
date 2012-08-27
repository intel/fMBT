/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012 Intel Corporation.
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

#include "coverage_min.hh"
#include "model.hh"
#include "helper.hh"

Coverage_Min::Coverage_Min(Log& l, std::string& _params) :
  Coverage(l), params(_params)
{
  static std::string separator(":");
  char* tmp=strdup(params.c_str());
  std::string m(unescape_string(tmp));
  std::vector<std::string> s;
  strvec(s,m,separator);
  free(tmp); 
  for(unsigned i=0;i+1<s.size();i+=2) {  
    Coverage* cov=CoverageFactory::create(log, s[i], s[i+1]);
    if (cov==NULL) {
      status=false;
      errormsg=std::string("Can't create coverage ")+s[i]+":"+s[i+1];
      return;
    }
    coverages.push_back(cov);
  }
}

void Coverage_Min::push()
{
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->push();
    }
  }
}

void Coverage_Min::pop()
{
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->pop();
    }
  }
}

void Coverage_Min::history(int action,
			   std::vector<int>& props, 
			   Verdict::Verdict verdict)
{
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->history(action,props,verdict);
    }
  }
}

bool Coverage_Min::execute(int action)
{
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->execute(action);
    }
  }
  return true;
}


float Coverage_Min::getCoverage()
{
  float ret=0.0;

  if (coverages.empty()) {
    return ret;
  }

  ret=coverages[0]->getCoverage();

  for(unsigned i=1;i<coverages.size();i++) {
    if (coverages[i]) {
      float tmp=coverages[i]->getCoverage();
      if (tmp<ret) {
	ret=tmp;
      }
    }
  }

  return ret;
}


int Coverage_Min::fitness(int* action,int n,float* fitness)
{
  float m=-1;
  int pos=-1;
  
  for(int i=0;i<n;i++) {
    model->push();
    model->execute(action[i]);
    fitness[i]=getCoverage();
    model->pop();

    if (m<fitness[i]) {
      pos=i;
      m=fitness[i];
    }
  }
  
  return pos;
}

void Coverage_Min::set_model(Model* _model) {
  Coverage::set_model(_model);
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->set_model(model);
    }
  }  
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Min, "min")
