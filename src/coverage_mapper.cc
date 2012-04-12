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
#include <cstring>
#include "dparse.h"
#include "rules.hh"
#include "coverage_mapper.hh"
#include "conf.hh"
#include "helper.hh"

#include <sstream>
#include <iostream>
#include <vector>

#ifndef DROI
#include <boost/regex.hpp>
#endif

extern "C" {
extern D_ParserTables parser_tables_mrules;
}

extern Rules* amobj;

Coverage_Mapper::Coverage_Mapper(Log& l, std::string params) :
  Coverage(l)
{
  load(params);
}

std::string Coverage_Mapper::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);
  std::multimap<int,coverage_action>::iterator it=m.begin();

  for(unsigned i=0;i<coverage_names.size();i++) {
    if (coverage_names[i]!=std::string("")) {
      t << i << "=\"" << coverage_names[i] << "\"" << std::endl;
    }
  }

  for(;it!=m.end();it++) {
    int cm=it->second.first;
    int ca=it->second.second;
    t << model->getActionName(it->first) << " -> (" 
      << cm << " \"" << models[cm]->getActionName(ca) << "\""
      << std::endl;
  }
  
  return t.str();
}

void Coverage_Mapper::push() {
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->push();
    }
  }
}

void Coverage_Mapper::pop() {
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      coverages[i]->pop();
    }
  }
}


void Coverage_Mapper::history(int action,
                             std::vector<int>& props, 
                             Verdict::Verdict verdict)
{
  std::pair<std::multimap<int,coverage_action>::iterator,
    std::multimap<int,coverage_action>::iterator> p = 
    m.equal_range(action);
  
  for (std::multimap<int,coverage_action>::iterator i = p.first;
       i != p.second;
       ++i) {
    coverages[i->second.first]->history(i->second.second,
					props,verdict);
  }
}

bool Coverage_Mapper::execute(int action)
{
  std::pair<std::multimap<int,coverage_action>::iterator,
    std::multimap<int,coverage_action>::iterator> p = 
    m.equal_range(action);
  
  for (std::multimap<int,coverage_action>::iterator i = p.first;
       i != p.second;
       ++i) {
    coverages[i->second.first]->execute(i->second.second);
    if (models[i->second.first]!=model) {
      models[i->second.first]->execute(i->second.second);
    }
  }
  return true; 
}

float Coverage_Mapper::getCoverage()
{
  int count=0;
  float ret=0;
  for(unsigned i=0;i<coverages.size();i++) {
    if (coverages[i]) {
      ret+=coverages[i]->getCoverage();
      count++;
    }
  }
  
  if (count) {
    return ret/count;
  }

  log.debug("Coverage_Mapper is constant 1\n");

  return 1;
}

int Coverage_Mapper::fitness(int* actions,int n, float* fitness)
{
  int ret=0;

  for(unsigned i=0;i<models.size();i++) {
    if (models[i]) {
      std::vector<int> cn(models[i]->getActionNames().size());
      std::vector<float> fn(models[i]->getActionNames().size());
      std::vector<int> bm(models[i]->getActionNames().size());

      int c = 0;

      for(int j=0;j<n;j++) {
	std::pair<std::multimap<int,coverage_action>::iterator,
	  std::multimap<int,coverage_action>::iterator> p = 
	  m.equal_range(actions[j]);
	for (std::multimap<int,coverage_action>::iterator it
	       = p.first;it != p.second;++it) {
	  if ((unsigned)it->second.first == i) {
	    cn[c]=it->second.second;
	    c++;
	    bm[c]=j;
	  }
	}
      }

      coverages[i]->fitness(&cn[0],c,&fn[0]);

      for(int j=0;j<c;j++) {
	if (bm[j]>0) {
	  fitness[bm[j]-1]+=fn[j];
	}
      }
    }
  }
  for(int i=0;i<n;i++) {
    if (fitness[i]>fitness[ret]) {
      ret=i;
    }
  }
  return ret;
}

void Coverage_Mapper::set_model(Model* _model)
{
  model=_model;
  pload(load_name);
  if (status) {
    for(int i=0;i<models.size();i++) {
      if (coverages[i]) 
	coverages[i]->set_model(models[i]);
    }
  }
}

bool Coverage_Mapper::load(std::string& name)
{
  load_name = name;
  return true;
}

bool Coverage_Mapper::pload(std::string& name)
{
  D_Parser *p = new_D_Parser(&parser_tables_mrules, 16);
  p->loc.pathname = name.c_str();
  char *s;

  log.debug("%s called\n",__func__);

  Rules* tmp=amobj;

  amobj=this;

  s=readfile(name.c_str());

  bool ret=dparse(p,s,std::strlen(s));

  ret=p->syntax_errors==0 && ret;

  free(s);
  free_D_Parser(p);
  amobj=tmp;

  if (ret) {
    log.debug("loading %s ok\n",name.c_str());
  } else {
    log.debug("loading %s failed\n",name.c_str());
    status=ret;
    return ret;
  }

  /* Time to load adapters */

  for(unsigned i=0;i<coverage_names.size();i++) {
    if (coverage_names[i]!=std::string("")) {

      log.debug("Loading coverage \"%s\"\n",
	     coverage_names[i].c_str());

      std::string coverage_class;
      std::string coverage_params;
      
      Conf::split(coverage_names[i],coverage_class,coverage_params);

      log.debug("class %s, params %i\n",
	     coverage_class.c_str(),
	     coverage_params.c_str());
      
      Coverage* a= CoverageFactory::create(log,coverage_class,
				    coverage_params);
      log.debug("Created coverage to %p\n",a);
      if (!a || !a->status) {
	status=false;
      }
      coverages[i] = a;
    }
  }

  return ret;
}


void Coverage_Mapper::add_file(unsigned index,
			       std::string& coveragename)
{
  log.debug("%s(%i,%s)\n",__func__,index,coveragename.c_str());
  if (coverage_names.capacity()<=index+1) {
    coverage_names.resize(index+2);
    coverages.resize(index+2);
    models.resize(index+2);
  }

  std::string cname;
  std::string mname;

  Conf::split(coveragename,mname,cname);

  unescape_string(cname);
  coverage_names[index]=std::string(cname);

  if (cname=="") {
    models[index] = model;
  } else {
    unescape_string(mname);
    std::string model_name;
    std::string model_param;

    Conf::split(mname, model_name, model_param);

    models[index] = ModelFactory::create(log,model_name,model_param);
    if (!models[index] || models[index]->status==false) {
      status=false;
      return;
    }
    models[index]->init();
    models[index]->reset();
  }
  std::string cc;
  std::string cp;

  Conf::split(cname,cc,cp);

  log.debug("Trying to create coverage %s(%s)\n",cc.c_str(),cp.c_str());
  coverages[index] = CoverageFactory::create(log,cc,cp);

  if (!coverages[index]) {
    status=false;
    return;
  }
  status&=coverages[index]->status;
}

void Coverage_Mapper::add_map(unsigned int index,std::string& n,int action) {
  log.debug("%s(%i,%s,%i)\n",__PRETTY_FUNCTION__,index,n.c_str(),
	 action);

  if (models.size()<=index ||
      models[index]==NULL) {
    /* No such model */
    errormsg=std::string("index ") + to_string(index) + std::string(" out of bounds");
    status=false;
    log.debug("No such model\n");
    return;
  }

  int an = models[index]->action_number(n);

  if (an < 0) { 
    /* No such action.. */
    errormsg=std::string("(") + to_string(index) + std::string("\"") + n + std::string("\") no such action");
    status=false;
    log.debug("No such action\n");
    return;
  }

  log.debug("%s %s %i\n",__func__,n.c_str(),an);

  m.insert(std::pair<int, coverage_action >(action,coverage_action(index,an)));
}

void Coverage_Mapper::add_result_action(std::string* name)
{
  if (!status) {
    return;
  }

  log.debug("%s(%s) called\n",__func__,name->c_str());

  int action=model->action_number(*name);


  log.debug("%s(%s) called\n",__func__,name->c_str());

  if (action==-1) {
#ifndef DROI
    std::vector<std::string>& actions=model->getActionNames();
    /* try regexp case */
    log.debug("Regexp case\n");
    const char* format_string = l_name.c_str();
    
    log.debug("Format string \"%s\"\n",format_string);

    boost::regex expression(*name);
    boost::cmatch what;

    for(unsigned int i=1;i<actions.size();i++) {
      log.debug("Action %s\n",actions[i].c_str());
      fflush(stdout);
      if(boost::regex_match(actions[i].c_str(), what, expression)) {
	/* Match */
	std::string s=replace(expression,l_name.c_str(),
		  actions[i].begin(),actions[i].end());
	add_map(l_index,s,i);
      }
    }
#endif
  } else {
    add_map(l_index,l_name,action);
  }
}
void Coverage_Mapper::add_component(unsigned index,
				    std::string& name,bool)
{
  if (!status) {
    return;
  }
  log.debug("%s(%i,%s)\n",__func__,index,name.c_str());

  if (index>=coverages.size() || coverages[index]==NULL) {

    log.debug("%i, %p\n",coverages.size(),coverages[index]);

    errormsg=std::string("index ") + to_string(index) + std::string(" out of bounds");
    status=false;
  }
  l_name=name;
  l_index=index;

}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Mapper, "mapper")
