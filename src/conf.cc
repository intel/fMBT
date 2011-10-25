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
  if (s==NULL) {
    log.debug("Can't load lts %s",name.c_str());
    throw (int)(42011);
  }

  bool ret=dparse(p,s,std::strlen(s));

  if (!ret) {
    log.debug("Error in parsing %s\n",name.c_str());
    return;
  }

  free(s);

  free_D_Parser(p);

  conf_obj=tmp;

  heuristic=Heuristic::create(log,heuristic_name);

  model=Model::create(log,filetype(model_name));

  if (!model->load(model_name)) {
    status=false;
  } else {
    model->reset();
  }

  Coverage* t = Coverage::create(log,coverage_name,coverage_param);

  heuristic->set_coverage(t);

  t->setmodel(model);

  adapter = Adapter::create(adapter_name,
			    model->getActionNames(),
			    adapter_param,log);

  heuristic->set_model(model);
  if (!t->status || !adapter->status) {
    status=false;
  }
  log.pop();
}

#include <sstream>

std::string Conf::stringify() {
  std::ostringstream t(std::ios::out | std::ios::binary);

  if (!status) {
    return std::string("");
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

  adapter->init();

  Test_engine engine(*heuristic,*adapter,log,policy);

  if (interactive || !engine.run(engine_cov,engine_count)) {
    engine.interactive();
  }

  log.pop();
}
