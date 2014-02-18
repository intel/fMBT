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

#ifndef __coverage_proxy_hh__
#define __coverage_proxy_hh__

#include "coverage.hh"
#include "coverage.hh"
#include "proxy.hh"

extern Proxy callback_proxy;

class Coverage_proxy : public Coverage, public Proxy {
public:
  Coverage_proxy(Log& l,Coverage* _c,const std::string& _n);

  virtual ~Coverage_proxy() {
    delete c;
    // Removeme...
    CoverageFactory::add_factory("old",NULL);    
  }

  virtual void push() {
    c->push();
    status=c->status;errormsg=c->errormsg;
  }
  virtual void pop() {
    c->pop();
    status=c->status;errormsg=c->errormsg;
  }

  virtual bool set_instance(int instance) {
    bool ret=c->set_instance(instance);
    status=c->status;errormsg=c->errormsg;
    return ret;
  }

  virtual void history(int action, std::vector<int>& props,
 		       Verdict::Verdict verdict) {
    c->history(action,props,verdict);
    status=c->status;errormsg=c->errormsg;
  }

  virtual bool execute(int action) {
    bool ret=c->execute(action);
    status=c->status;errormsg=c->errormsg;
    return ret;
  }

  virtual float getCoverage() {
    float ret=c->getCoverage();
    status=c->status;errormsg=c->errormsg;
    return ret;
  }

  virtual std::string stringify() {
    return c->stringify();
  }

  virtual int fitness(int* actions,int n, float* fitness) {
    int ret= c->fitness(actions,n,fitness);
    status=c->status;errormsg=c->errormsg;
    return ret;
  }

  virtual void set_model(Model* _model) {
    Coverage::set_model(_model);
    c->set_model(model);
    status=c->status;errormsg=c->errormsg;
  }

  static Coverage* old_coverage;

protected:

  bool get(std::string params,std::string& ret_str) {
    log.debug("Kutsuttiin coverage_proxy:n get-metodia!\n");
    if (c) {
      ret_str=name;
    } else {
      ret_str="";
    }
    return true;
  }
  
  bool set(std::string params,std::string& ret_str) {
    Coverage* cc=new_coverage(log,params);
    log.debug("Kutsuttiin coverage_proxy:n set-metodia!\n");
    if (cc) {
      name=params;
      delete c;
      c=cc;
      c->set_model(model);
      status=c->status;errormsg=c->errormsg;
      ret_str="True";
      old_coverage=c;
    } else {
      ret_str="False";
    }
    return true;
  }

  bool get_value(std::string params,std::string& ret_str);

  Coverage* c;
  std::string name;
};

#endif
