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

#include "heuristic_coverage_random.hh"
#include "coverage_random.hh"

#include "helper.hh"
#include <cstdlib>
#include <cstring>
#include <algorithm>

#include "random.hh"
#include "function.hh"

Heuristic_coverage_random::Heuristic_coverage_random(Log& l,const std::string& params) :
  Heuristic(l),h(NULL),sub_coverage(NULL),var(0.1),r(NULL)
{
  std::vector<std::string> subs;
  commalist(params,subs);  
  // varianse, random, sub
  if (subs.size()>3) {
    status=false;
    errormsg="Too many parameters";
    return;
  }

  if (subs.size()==3) {
    r=new_random(subs[2]);
    if (!r) {
      status=false;
      errormsg="Can't create random "+subs[2];
      return;
    }

    l.push("Heuristic=coverage_random");
    l.print("<random init=\"%s\"/>\n",r->stringify().c_str());
    l.pop();

  }

  if (subs.size()>1) {
    Function* f = new_function(subs[1]);
    if (!f) {
      status=false;
      errormsg = "Does not compute " + subs[1];
    } else {
      if (!f->status) {
	status=false;
	errormsg=f->errormsg;
      } else {
	// We have something!
	var = f->fval();
      }
      delete f;
    }
  }
  
  
  if (!r) {
    r=Random::default_random();
    // default random
  }

  if (!r->status) {
    status=false;
    errormsg+=r->errormsg;
  }

  h = new_heuristic(l,subs[0]);

  if (!h) {
    errormsg="Can't create heuristic "+subs[0];
    status=false;
    return;
  }

  if (!h->status) {
    errormsg=h->errormsg;
    status=false;
  }

}

Heuristic_coverage_random::~Heuristic_coverage_random()
{
  if (sub_coverage)
    delete sub_coverage;
  if (h)
    delete h;
  if (r)
    r->unref();
}

int Heuristic_coverage_random::getAction()
{
  int ret=h->getAction();
  if (!h->status) {
    status=false;
    errormsg=h->errormsg;
  }
  return ret;
}

int Heuristic_coverage_random::getIAction()
{
  int ret=h->getIAction();
  if (!h->status) {
    status=false;
    errormsg=h->errormsg;
  }
  return ret;
}

void Heuristic_coverage_random::set_model(Model* _model)
{
  Heuristic::set_model(_model);
  if (sub_coverage) 
    sub_coverage->set_model(model);
  if (h) 
    h->set_model(model);
}

void Heuristic_coverage_random::set_coverage(Coverage* c)
{
  Heuristic::set_coverage(c);
  // Sub coverage create...
  sub_coverage=new Coverage_random(log,my_coverage,var,r);
  h->set_coverage(sub_coverage);
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_coverage_random, "coverage_random")
