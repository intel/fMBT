/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011,2012 Intel Corporation.
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

#include "of.hh"

#undef FACTORY_CREATE_PARAMS
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2

#define FACTORY_CREATE_PARAMS std::string name, std::string params
#define FACTORY_CREATOR_PARAMS std::string params
#define FACTORY_CREATOR_PARAMS2 params

FACTORY_IMPLEMENTATION(OutputFormat)

#undef FACTORY_CREATE_PARAMS
#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#undef __factory_h__

#include "conf.hh"
#include "log.hh"
#include "helper.hh"
#include "history_log.hh"
#include "coverage_of.hh"
#include "coverage_notice.hh"

OutputFormat::~OutputFormat() {
  for(unsigned i=0;i<covs.size();i++) {
    delete covs[i];
  }

  for(unsigned i=0;i<rcovs.size();i++) {
    delete rcovs[i];
  }

  for(unsigned i=0;i<testruns.size();i++) {
    delete testruns[i];
  }

  if (model)
    delete model;

  model=NULL;

  
}

void OutputFormat::set_model(Model* m) {
  model=m;

  if (status) {
    for(unsigned int i=0;i<covs.size();i++) {
      if (covs[i]) {
	covs[i]->set_model(model);
	if (covs[i]->status==false) {
	  status=false;
	  errormsg=errormsg+" "+covs[i]->errormsg;
	}
      }
    }
  }

  if (status) {
    for(unsigned int i=0;i<rcovs.size();i++) {
      if (rcovs[i]) {
	rcovs[i]->set_model(model);
	if (rcovs[i]->status==false) {
	  status=false;
	  errormsg=errormsg+" "+rcovs[i]->errormsg;
	}
      }
    }
  }

}

void OutputFormat::set_model(std::string m)
{
  return;
  /*
  if (status) {

    if ((model=new_model(l,m)) == NULL)
      {
	errormsg="Can't create model \""+m+"\"";
	status=false;
	return;
      } else {
      if (model->status && model->init()) {
	set_model(model);
      } else {
	status=false;
	errormsg="Model error "+model->errormsg;
      }
    }
  } else {
  }
  */
}


void OutputFormat::add_uc(std::string& name,
			  Coverage* c)
{
  if (status) {
    if (c->status) {
      covnames.push_back(name);
      covs.push_back(c);
      // c->set_model(model);
    } else {
      status=false;
      errormsg=errormsg+"coverage \""+ name  + "\": "+c->errormsg;
    }
  }
}


std::string OutputFormat::handle_history(Log&l,std::string& h)
{
  if (status) {
    test_verdict="N/A";
    History* history = new History_log(l,h);
    std::vector<Coverage*> c;
    c.insert(c.end(),rcovs.begin(),rcovs.end());
    c.insert(c.end(),covs.begin(),covs.end());
    Coverage_of* cov=new Coverage_of(l,c);

    testnames.push_back(h);

    Alphabet* al=history->set_coverage(cov,model);

    if (al) {
      model=dynamic_cast<Model*>(al);
    }

    test_verdict=history->test_verdict;

    delete cov;
    delete history;
    return format_covs();
  } else {
    return "";
  }
}

void OutputFormat::add_uc(std::string& name,
			  std::string& c)
{
  if (status) {
    Coverage* coverage = new_coverage(l,c);
    if (coverage == NULL) {
      errormsg="Can't create coverage";
      status=false;
    } else {
      add_uc(name,coverage);
    }
  }
}

void OutputFormat::add_notice(std::string& name,
			      std::string& cov)
{
  if (status) {
    reportnames.push_back(name);
    Coverage_report* c=new Coverage_notice(l,cov,std::string(""));
    if (c->status==false) {
      status=false;
      errormsg=errormsg+" Report failure:"+c->errormsg;
    } else {
      // c->set_model(model);
    }
    rcovs.push_back(c);
  }
}

void OutputFormat::add_report(std::string& name,
			      std::vector<std::string*>& from,
			      std::vector<std::string*>& to,
			      std::vector<std::string*>& drop)
{
  if (status) {
    reportnames.push_back(name);
    Coverage_report* c=new Coverage_report(l,from,to,drop);
    if (c->status==false) {
      status=false;
      errormsg=errormsg+" Report failure:"+c->errormsg;
    } else {
      // c->set_model(model);
    }
    rcovs.push_back(c);
  }
}


void OutputFormat::add_testrun(std::string& name,
			       std::string& _model)
{
  if (status) {

    Model* model;
    if ((model=new_model(l, _model)) == NULL) {
      errormsg="Can't create model \""+_model+"\"";
      status=false;
    } else {
      if (model->status) {
	add_testrun(name,model);
      } else {
	status=false;
	errormsg="Model error "+model->errormsg;
      }
    }
  }
}

void OutputFormat::add_testrun(std::string& name,
			       Model* _model)
{
  if (status) {
    testruns.push_back(_model);
    testnames.push_back(name);
  }
}
