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

#ifndef __heuristic_proxy_hh__
#define __heuristic_proxy_hh__

#include "heuristic.hh"
#include "coverage.hh"
#include "proxy.hh"
#include "learning.hh"

extern Proxy callback_proxy;

class Heuristic_proxy : public Heuristic, public Proxy {
public:
  Heuristic_proxy(Log& l,Heuristic* _h,const std::string& _n);

  virtual ~Heuristic_proxy() {
    if (h) {
      HeuristicFactory::remove_factory("old");
      delete h;
    }
  }

  virtual bool execute(int action) {
    bool ret= h->execute(action);
    status=h->status;errormsg=h->errormsg;

    if (status && ret && learn) {
      learn->execute(action);
    }

    return ret;
  }

  virtual float getCoverage() {
    float ret= h->getCoverage();
    status=h->status;errormsg=h->errormsg;
    return ret;
  }

  virtual int getAction() {
    int ret= h->getAction();
    status=h->status;errormsg=h->errormsg;
    return ret;
  }

  virtual int getIAction() {
    int ret= h->getIAction();
    status=h->status;errormsg=h->errormsg;
    if (status && ret>0 && learn) {
      learn->suggest(ret);
    }
    return ret;
  }

  virtual void set_coverage(Coverage* c) {
    Heuristic::set_coverage(c);
    h->set_coverage(c);
    status=h->status;errormsg=h->errormsg;
  }

  virtual void set_learn(Learning* _learn) {
    Heuristic::set_learn(_learn);
    h->set_learn(learn);
  }

  virtual void set_model(Model* _model) {
    Heuristic::set_model(_model);
    h->set_model(model);
    status=h->status;errormsg=h->errormsg;
  }

  static Heuristic* old_heuristic;

protected:

  bool get(std::string params,std::string& ret_str) {
    if (h) {
      ret_str=name;
    } else {
      ret_str="";
    }
    return true;
  }

  bool set(std::string params,std::string& ret_str) {
    Heuristic* hh=new_heuristic(log,params);
    if (hh) {
      name=params;
      delete h;
      h=hh;
      h->set_model(model);
      h->set_coverage(my_coverage);
      ret_str="True";
    } else {
      ret_str="False";
    }
    return true;
  }

  Heuristic* h;
  std::string name;
};

#endif
