/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2013, Intel Corporation.
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

#include "coverage_notice.hh"
#include "history.hh"
#include <algorithm>

static std::vector<std::string*> dummy;

std::string _stmp("1");

Coverage_notice::Coverage_notice(Log&l,std::string _cc1,std::string _cc2):
  Coverage_report(l,dummy,dummy,dummy),cc1(_cc1),cc2(_cc2),const1(l,_stmp)
{
  
}

Coverage_notice::~Coverage_notice() 
{
  std::list<std::pair<std::pair<Coverage*,Coverage*>,
		      std::pair<
			std::pair<struct timeval,struct timeval>,
			std::vector<std::pair<int,std::vector<int> > > > > >::iterator i;
  for(i=subcovs.begin();i!=subcovs.end();i++) {
    delete i->first.first;
    if (i->first.second != &const1) {
      delete i->first.second;
    }
  }
}


void Coverage_notice::foo()
{
  Coverage* c1;
  Coverage* c2;
  if (cc2=="") {
    c2=&const1;
  } else {
    c2=new_coverage(log,cc2);
    if (c2==NULL) {
      status=false;
      errormsg="Can't create coverage \""+cc2+"\"";
      return;
    }
    c2->set_model(model);
  }
  c1=new_coverage(log,cc1);

  if (c1==NULL) {
    status=false;
    errormsg="Can't create coverage \""+cc1+"\"";
    return;
  }
  c1->on_report=true;
  c1->set_model(model);

  if (!c1->status) {
    status=false;
    errormsg="Submodel failure \""+cc1+"\":"+c1->errormsg;
    return;
  }

  if (!c2->status) {
    status=false;
    errormsg="Submodel failure \""+cc2+"\":"+c2->errormsg;
  }

  std::vector<std::pair<int,std::vector<int> > > m;
  
  subcovs.push_front(std::pair<std::pair<Coverage*,Coverage*>,
				  std::pair<std::pair<struct timeval,struct timeval>,
					    std::vector<std::pair<int,std::vector<int> > > > >
  (std::pair<Coverage*,Coverage*>(c1,c2),
   std::pair<std::pair<struct timeval,struct timeval>,std::vector<std::pair<int,std::vector<int> > > >
   ( std::pair<struct timeval,struct timeval>(History::current_time,History::current_time),m)));

}

bool Coverage_notice::execute(int action)
{
  if (action<=0) {
    return true;
  }
  struct execute_class {
    void operator() (std::pair<std::pair<Coverage*,Coverage*>,
			       std::pair<
				 std::pair<timeval,timeval>,
				 std::vector<std::pair<int,std::vector<int> > > > > &
		     cpair) {
      float f=cpair.first .first ->getCoverage();
      
      cpair.first .first ->execute(action);
      cpair.first .second->execute(action);

      float f1=cpair.first .first ->getCoverage();
      float f2=cpair.first .second->getCoverage();

      if (f==0.0 && f1>0) {
	// Start of the trace
	cpair.second.first.first=History::current_time;
	// We need to create an other instance...
	r->foo();	
      }

      if (f1>0) {
	std::vector<int> t;
	cpair.second.second.push_back(std::pair<int,std::vector<int> >(action,t));
	if (f1>=f2) {
	  r->log.debug("coverage passed... %04f %04f\n",f1,f2);

	  cpair.second.first.second=History::current_time;
	  // trace found!

	  r->traces.push_back(cpair.second.second);
	  r->tcount[cpair.second.second]++;

	  r->times.push_back(cpair.second.first);

	  // Ok. We can delete the coverage objects.
	  delete cpair.first .first;
	  if (cpair.first .second != & r->const1) {
	    delete cpair.first.second;
	  }
	  cpair.first.first =NULL;
	  cpair.first.second=NULL;
	  // Now we need to erase iterator.
	}
      } else {
	// ??
      }
    }
    int action;
    Model* model;
    Coverage_notice* r;
  } callobject;

  callobject.action=action;
  callobject.model =model;
  callobject.r     =this;

  int ff=0;
  
  std::list<std::pair<std::pair<Coverage*,Coverage*>,
		      std::pair<
			std::pair<struct timeval,struct timeval>,
			std::vector<std::pair<int,std::vector<int> > > > > >
    ::iterator i1;

  //for_each(subcovs.begin(),subcovs.end(),callobject);
  //for_each doesn't work for some reason and I'm too lazy to figure out why. Most likely it's my fault.

  for(i1=subcovs.begin();i1!=subcovs.end();i1++) {
    ff++;
    callobject(*i1);
  }

  // Delete handled elements...
  for(i1=subcovs.begin();i1!=subcovs.end();) {
    if (i1->first.first) {
      i1++;
    } else {
      i1=subcovs.erase(i1);
    }
  }
  return true;
}
