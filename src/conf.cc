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
#include "conf.hh"
#include "dparse.h"
#include <cstring>

extern "C" {
extern D_ParserTables parser_tables_conf;
};

extern Conf* conf_obj;

#define RETURN_ERROR(s) { \
  status=false; \
  errormsg=s; \
  return; \
  }

void Conf::split(std::string& val,std::string& name,
			std::string& param)
{
  
   unsigned long cutpos = val.find_first_of(":");
  
  if (cutpos == val.npos) {
    name  = val;
    param = std::string("");
  } else { 
    name  = val.substr(0,cutpos);   
    param = val.substr(cutpos+1);
  }
}


void Conf::load(std::string& name)
{
  D_Parser *p = new_D_Parser(&parser_tables_conf, 512);
  char *s;
  
  Conf* tmp=conf_obj;
  log.push("conf_load");
  log.debug("Conf::load %s",name.c_str());
  conf_obj=this;

  s=readfile(name.c_str());
  if (s==NULL)
    RETURN_ERROR("Loading \"" + name + "\" failed.");

  bool ret=dparse(p,s,std::strlen(s));

  if (!ret)
    RETURN_ERROR("Parsing \"" + name + "\" failed.");

  free(s);

  free_D_Parser(p);

  conf_obj=tmp;

  if ((heuristic=Heuristic::create(log, heuristic_name)) == NULL)
    RETURN_ERROR("Creating heuristic \"" + heuristic_name + "\" failed.");

  if ((model=Model::create(log,filetype(model_name))) == NULL)
    RETURN_ERROR("Creating model loader \"" + filetype(model_name)
                 + "\" failed.");

  Coverage* coverage = Coverage::create(log,coverage_name,coverage_param);
  if (coverage == NULL)
    RETURN_ERROR("Creating coverage \"" + coverage_name + "\" failed.");

  if (!model->load(model_name))
    RETURN_ERROR("Loading model \"" + model_name + "\" failed.");

  model->reset();

  heuristic->set_coverage(coverage);

  heuristic->set_model(model);

  coverage->set_model(model);

  adapter = AdapterFactory::create(log, adapter_name, adapter_param);

  if (adapter == NULL)
    RETURN_ERROR("Creating adapter \"" + adapter_name + "\" failed.");

  adapter->set_actions(&model->getActionNames());

  if (!coverage->status)
    RETURN_ERROR("Coverage error: " + coverage->stringify());

  if (!adapter->status)
    RETURN_ERROR("Adapter error: " + adapter->stringify());

  log.pop();
}

#include <sstream>

std::string Conf::stringify() {
  std::ostringstream t(std::ios::out | std::ios::binary);

  if (!status) {
    return errormsg;
  }

  t << "model = \"" << removehash(model_name) << capsulate(model->stringify()) << std::endl;
  t << "heuristic = \"" << heuristic_name << "\"" << std::endl;
  t << "coverage = \"" <<  coverage_name << "\"" << std::endl;
  t << "adapter = \"" << removehash(adapter_name) << ":"
    << removehash(adapter_param)
    << capsulate(adapter->stringify()) << std::endl;

  t << "engine.cov = " << engine_cov << std::endl;
  t << "engine.count = " << engine_count << std::endl;

  return t.str();
}

void Conf::execute(bool interactive) {

  Policy policy;
  log.push("conf_execute");

  if (!status) {
    return;
  }

  if (!adapter->init())
    RETURN_ERROR("Initialising adapter failed: " + adapter->stringify());

  Test_engine engine(*heuristic,*adapter,log,policy);

  if (interactive || !engine.run(engine_cov,engine_count)) {
    engine.interactive();
  }

  log.pop();
}
