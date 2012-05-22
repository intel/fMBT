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

OutputFormat::~OutputFormat() {}

void OutputFormat::set_model(std::string m)
{ 
  if (status) {
    std::string model_name;
    std::string model_param;
    
    split(m, model_name, model_param);

    printf("load model %s %s\n",model_name.c_str(),model_param.c_str());
    
    if ((model=Model::create(l,model_name,model_param)) == NULL)
      {
	errormsg="Can't create model \""+m+"\"";
	status=false;
	return;
      } else {
      if (model->status) {
	set_model(model);
      } else {
	status=false;
	errormsg="Model error "+model->errormsg;
      }
    }
  }
}


void OutputFormat::add_uc(std::string& name,
			  Coverage* c)
{
  if (status) {
    covnames.push_back(name);
    covs.push_back(c);
    c->set_model(model);
  }
}


std::string OutputFormat::handle_history(Log&l,std::string& h)
{
  if (status) {
    History* history = new History_log(l,h);
    std::vector<Coverage*> c;
    c.resize(rcovs.size());
    std::copy(rcovs.begin(),rcovs.end(),c.begin());
    Coverage_of* cov=new Coverage_of(l,c);
    
    testnames.push_back(h);
    
    history->set_coverage(cov,model);
    return format_covs();
  } else {
    return "";
  }
}

void OutputFormat::add_uc(std::string& name,
			  std::string& c)
{
  if (status) {
    std::string coverage_name;
    std::string coverage_param;
    split(c, coverage_name, coverage_param);  
    
    Coverage* coverage = CoverageFactory::create(l,coverage_name,coverage_param);
    if (coverage == NULL) {
      errormsg="Can't create coverage";
      status=false;
    } else {
      add_uc(name,coverage);
    }
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
    c->set_model(model);
    rcovs.push_back(c);
  }
}


void OutputFormat::add_testrun(std::string& name,
			       std::string& _model)
{
  if (status) {
    std::string model_name,model_param;
    split(_model, model_name, model_param);

    Model* model;
    if ((model=Model::create(l, model_name, model_param)) == NULL) {
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
