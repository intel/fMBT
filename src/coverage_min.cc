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

Coverage_Min::Coverage_Min(Log& l,const std::string& _params,unit* _u) :
  Coverage(l), params(_params),u(_u)
{
  std::vector<std::string> s;
  commalist(params,s);

  for(unsigned i=0;i<s.size();i++) {
    Coverage* cov=new_coverage(log,s[i]);
    if (cov==NULL) {
      status=false;
      errormsg=std::string("Can't create coverage "+s[i]);
      return;
    }
    coverages.push_back(cov);
    if (!cov->status) {
      status=false;
      errormsg="coverage error at "+s[i]+ ": "+ cov->errormsg;
      return;
    }
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

  u->next(coverages[0]->getCoverage(),true);

  for(unsigned i=1;i<coverages.size();i++) {
    if (coverages[i]) {
      u->next(coverages[i]->getCoverage(),false);
    }
  }

  return u->value();
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
  for(unsigned i=0;i<coverages.size()&&status;i++) {
    if (coverages[i]) {
      coverages[i]->set_model(model);
      if (!(coverages[i]->status)) {
	errormsg=coverages[i]->errormsg;
	status=false;
      }
    }
  }
}

namespace {
  Coverage* min_creator_func( Log& log,const std::string params,void*)
  {
    return new Coverage_Min(log, params,new Coverage_Min::unit_min);
  }

  Coverage* max_creator_func( Log& log, std::string params,void*)
  {
    return new Coverage_Min(log, params,new Coverage_Min::unit_max);
  }

  Coverage* sum_creator_func( Log& log, std::string params,void*)
  {
    return new Coverage_Min(log, params,new Coverage_Min::unit_sum);
  }

  static CoverageFactory::Register memin("min", min_creator_func);
  static CoverageFactory::Register memax("max", max_creator_func);
  static CoverageFactory::Register mesum("sum", sum_creator_func);
}
