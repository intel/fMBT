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

#include "heuristic_include.hh"
#include <stdlib.h>

class Heuristic_include : public Heuristic_include_base {
public:
  Heuristic_include(Log&l,const std::string& params):
    Heuristic_include_base(l,params,false) {
  }
};

class Heuristic_exclude : public Heuristic_include_base {
public:

  Heuristic_exclude(Log&l,const std::string& params): Heuristic_include_base(l,params,true) {
  }
};


Heuristic_include_base::Heuristic_include_base(Log& l,const std::string& params,bool invert) :
  Heuristic(l), exclude(invert),child(NULL),hr(l,""),mf(l,params,invert)
{
  if (mf.fa.size()>=2) {
    child=new_heuristic(l,mf.fa[mf.fa.size()-1]);
    if (child && child->status) {
      status=true;
    } else {
      status=false;
    }
  } else {
    status=false;
  }
}

void Heuristic_include_base::set_coverage(Coverage* c)
{
  Heuristic::set_coverage(c);
  if (child) {
    child->set_coverage(c);
  }
  hr.set_coverage(c);
}

void Heuristic_include_base::set_model(Model* _model)
{
  Heuristic::set_model(_model);
  mf.submodel=_model;
  mf.init();
  hr.set_model(_model);
  if (child) {
    child->set_model(&mf);
  }
}

float Heuristic_include_base::getCoverage() {
  if (child) {
    return child->getCoverage();
  }
  return 0.0;
}

int Heuristic_include_base::getAction()
{
  int ret=Alphabet::SILENCE;

  if (child) {
    ret=child->getAction();
  }

  if (ret==Alphabet::SILENCE || ret==Alphabet::DEADLOCK) {
    ret = hr.getAction();
  }

  return ret;
}

int Heuristic_include_base::getIAction()
{
  int i=Alphabet::SILENCE;

  if (child) {
    i=child->getIAction();
  }

  if (i==Alphabet::SILENCE || i==Alphabet::DEADLOCK) {
    i=hr.getIAction();
  }

  return i;
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_include, "include")
FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_exclude, "exclude")
