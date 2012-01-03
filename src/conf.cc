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
#include "helper.hh"
#include "history.hh"
#include <cstring>

#ifndef DROI
#include <glib.h>
#else

#endif

extern "C" {
extern D_ParserTables parser_tables_conf;
}

extern Conf* conf_obj;

#define RETURN_ERROR(s) { \
  log.pop();    \
  status=false; \
  errormsg=s;   \
  return;       \
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

  if ((heuristic=HeuristicFactory::create(log, heuristic_name, heuristic_param)) == NULL)
    RETURN_ERROR("Creating heuristic \"" + heuristic_name + "\" failed.");

  if ((model=ModelFactory::create(log,model_name,model_param)) == NULL)
      if ((model=ModelFactory::create(log,filetype(model_name),"")) == NULL)
          RETURN_ERROR("Creating model loader \"" + filetype(model_name)
                       + "\" failed.");

  Coverage* coverage = CoverageFactory::create(log,coverage_name,coverage_param);
  if (coverage == NULL)
    RETURN_ERROR("Creating coverage \"" + coverage_name + "\" failed.");

  if (!model->load(model_name))
    RETURN_ERROR("Loading model \"" + model_name + "\" failed: " + model->errormsg);

  model->reset();

  heuristic->set_coverage(coverage);

  heuristic->set_model(model);

  coverage->set_model(model);

  adapter = AdapterFactory::create(log, adapter_name, adapter_param);

  if (adapter && !adapter->status) {
    status=false;
    errormsg=adapter->errormsg;
    return;
  }

  /* handle history */
  for(unsigned i=0;i<history.size();i++) {
    std::string name,param;
    split(*history[i],name,param);

    History* h=HistoryFactory::create(log, name, param);
    
    if (h) {
      h->set_coverage(coverage,model);
      if (!h->status) {
	RETURN_ERROR(h->errormsg);
      }
    } else {
      RETURN_ERROR("Creating history \""+ *history[i] + "\" failed");
    }
  }

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
  int engine_tag=-1;
  log.push("conf_execute");

  if (!status) {
    return;
  }

  if (!adapter->init())
    RETURN_ERROR("Initialising adapter failed: " + adapter->stringify());

  Test_engine engine(*heuristic,*adapter,log,policy);

  if (status && model && exit_tag!="") {
    engine_tag=find(model->getSPNames(),exit_tag);
  }

  if (interactive) {
    engine.interactive();
  } else {
    if (!engine.run(engine_cov,engine_count,engine_tag,end_time)) {
      // Test failed. Continue according to the on_error
      // configuration. In addition to the following it could at
      // somepoint specify a shell command (for instance, package and
      // send log files, etc.)
      if (on_error == "interactive")
        engine.interactive();
      else
        RETURN_ERROR("Test failed.");
    }
    // Test passed
  }
  log.pop();
}

#ifndef DROI
void Conf::set_end_time(std::string &s)
{
  char* out=NULL;
  int stat;

  std::string ss="date --date='"+s+"' +%s";

  end_time=-1;

  if (g_spawn_command_line_sync(ss.c_str(),&out,NULL,&stat,NULL)) {
    if (!stat) {
      end_time=atoi(out);
    } else {
    }
  } else {
    status=false;
  }
}
#else
void Conf::set_end_time(std::string &s)
{
  char* endp;
  long r=strtol(s.c_str(),&endp,10);

  if (*endp==0) {
    end_time=r;
  } else {
    // Error on str?
    status=false;
  }

}
#endif
