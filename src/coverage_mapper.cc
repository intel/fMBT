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

#include <sstream>
#include <iostream>

#ifndef DROI
#include <boost/regex.hpp>
#endif

extern "C" {
extern D_ParserTables parser_tables_mrules;
};

extern Rules* amobj;

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

bool Coverage_Mapper::execute(int action)
{
  std::pair<std::multimap<int,coverage_action>::iterator,
    std::multimap<int,coverage_action>::iterator> p = 
    m.equal_range(action);
  
  for (std::multimap<int,coverage_action>::iterator i = p.first;
       i != p.second;
       ++i) {
    coverages[i->second.first]->execute(i->second.second);
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
      int cn[models[i]->getActionNames().size()];
      float fn[models[i]->getActionNames().size()];
      int bm[models[i]->getActionNames().size()];

      int c;

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

      coverages[i]->fitness(cn,c,fn);

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

void Coverage_Mapper::setmodel(Model* _model)
{
  model=_model;
  pload(load_name);
}

bool Coverage_Mapper::load(std::string& name)
{
  load_name = name;
  return true;
}

bool Coverage_Mapper::pload(std::string& name)
{
  D_Parser *p = new_D_Parser(&parser_tables_mrules, 16);
  char *s;

  log.debug("%s called\n",__func__);

  Rules* tmp=amobj;

  amobj=this;

  s=readfile(name.c_str());

  bool ret=dparse(p,s,std::strlen(s));

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
      
      Coverage* a= Coverage::create(log,coverage_class,
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

  coverage_names[index]=std::string(cname);
  models[index] = Model::create(log,filetype(mname));
  models[index]->load(mname);
  models[index]->reset();

  std::string cc;
  std::string cp;

  Conf::split(cname,cc,cp);
  log.debug("Trying to create coverage %s(%s)\n",cc.c_str(),cp.c_str());
  coverages[index] = Coverage::create(log,cc,cp);
  coverages[index]->setmodel(models[index]);
  
}

void Coverage_Mapper::add_map(unsigned int index,std::string& n,int action) {

  log.debug("%s(%i,%s,%i)\n",__PRETTY_FUNCTION__,index,n.c_str(),
	 action);

  if (models.size()<=index ||
      models[index]==NULL) {
    /* No such model */
    log.debug("No such model\n");
    return;
  }

  int an = models[index]->action_number(n);

  if (an < 0) { 
    /* No such action.. */
    log.debug("No such action\n");
    return;
  }

  log.debug("%s %s %i\n",__func__,n.c_str(),an);

  m.insert(std::pair<int, coverage_action >(action,coverage_action(index,an)));
}

void Coverage_Mapper::add_result_action(std::string* name)
{
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
	//log.debug("MATCH (%s %s)\n",actions[i].c_str(),name->c_str());
	std::ostringstream t(std::ios::out | std::ios::binary);
	std::ostream_iterator<char> oi(t);
	std::string s;
	boost::regex_replace(oi,actions[i].begin(),actions[i].end(),expression,format_string, boost::match_default | boost::format_all);

	std::cout << std::endl;

	s=t.str();

	add_map(l_index,s,i);

      }
    }
#endif
  } else {
    add_map(l_index,l_name,action);
  }
}
void Coverage_Mapper::add_component(unsigned index,
				    std::string& name)
{
  log.debug("%s(%i,%s)\n",__func__,index,name.c_str());

  if (index>=coverages.size() || coverages[index]==NULL) {

    log.debug("%i, %p\n",coverages.size(),coverages[index]);

    throw((int)4202);    
  }
  l_name=name;
  l_index=index;

}

namespace {
  Coverage* coverage_creator(Log&l,std::string& name) {
    Coverage_Mapper* r = new Coverage_Mapper(l);
    r->load(name);
    return r;
  }
  static Coverage_Creator coverage_foo("mapper",coverage_creator);
};
