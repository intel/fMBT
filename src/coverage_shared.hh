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
#ifndef __coverage_shared_hh__
#define __coverage_shared_hh__

#include <sys/time.h>
#include <stack>
#include <utility>

#include "coverage.hh"
#include "remote.hh"
#include "helper.hh"
#include "glib.h"

class Coverage_shared: public Coverage, public remote {
public:
  Coverage_shared(Log&l, std::string& params): 
    Coverage(l),
    remote(),
    push_depth(0),
    child(NULL)

  {
    std::vector<std::string> subs;
    commalist(params,subs);
    if (subs.size()==2) {
      child=new_coverage(l,subs[1]);
      if (!child) {
	status=false;
	errormsg="Can't create coverage \""+subs[1]+"\"";
      } else {
	if (!child->status) {
	  status=false;
	  errormsg=child->errormsg;
	}
      }
      if (status) {
	if (!child->set_instance(0)) {
	  status=false;
	  errormsg="Coverage \""+ subs[1] +"\" doesn't support shared coverage";
	  return;
	}

	// Create remote connection.
	int _stdin,_stdout,_stderr;
	//g_type_init ();
	
	gchar **argv = NULL;
	gint argc;
	GError *gerr=NULL;
	
	g_shell_parse_argv(prm.c_str(),&argc,&argv,&gerr);
	
	if (gerr) {
	  errormsg = "coverage shared: g_shell_parse_argv error: " + std::string(gerr->message)
	    + " when parsing " + prm;
	  log.debug(errormsg.c_str());
	  status = false;
	  return;
	}
	
	g_spawn_async_with_pipes(NULL,argv,NULL,(GSpawnFlags)(G_SPAWN_SEARCH_PATH|G_SPAWN_DO_NOT_REAP_CHILD),NULL,NULL,&pid,&_stdin,&_stdout,&_stderr,&gerr);
	
	for(int i=0;i<argc;i++) {
	  if (argv[i]) {
	    free(argv[i]);
	  }
	}
	free(argv);
	
	if (gerr) {
	  errormsg = "coverage shared g_spawn_async_with_pipes error: " + std::string(gerr->message);
	  log.debug(errormsg.c_str());
	  status = false;
	  return;
	}
	
	prefix="shared("+prm+")";
	
	monitor();
	
	d_stdin=g_io_channel_unix_new(_stdin);  
	d_stdout=g_io_channel_unix_new(_stdout);
	d_stderr=g_io_channel_unix_new(_stderr);

      }
    } else {
      status=false;
      errormsg="expected 2 parameters, got "+to_string((int)subs.size());
    }
  }

  virtual bool execute(int action) {
    if (push_depth==0) {
      // Handle the communication
      communicate(action);
    }

    return child->execute(action);
  }

  virtual ~Coverage_shared() {
    if (child) 
      delete child;
  }

  virtual void set_model(Model* _model) {
    Coverage::set_model(_model);

    if (child)
      child->set_model(_model);

    std::vector<std::string>& an=model->getActionNames();
    std::vector<std::string>& sn=model->getSPNames();

    // send action names
    
    fprintf(d_stdin,"%i\n",an.size());
    for(unsigned i=0;i<an.size();i++) {
      char* s=g_uri_escape_string(an[i].c_str(),
                                  NULL,false);
      fprintf(d_stdin,"%s\n",s);
      g_free(s);
    }

    // send tag names

    fprintf(d_stdin,"%i\n",sn.size());
    for(unsigned i=0;i<sn.size();i++) {
      char* s=g_uri_escape_string(sn[i].c_str(),
                                  NULL,false);
      fprintf(d_stdin,"%s\n",s);
      g_free(s);
    }
    
    
  }

  virtual std::string stringify() {
    return errormsg;
  }

  virtual void push() {
    push_depth++;
    child->push();
  }

  virtual void pop() {
    push_depth--;
    child->pop();
  }

  virtual float getCoverage() { return child->getCoverage(); }

  virtual int fitness(int* actions,int n, float* fitness) {
    return child->fitness(actions,n,fitness);
  }
protected:
  void communicate(int action);
  void receive_from_server();

  int push_depth;
  Coverage* child;

  GIOChannel* d_stdin;
  GIOChannel* d_stdout;
  GIOChannel* d_stderr;
  std::string prm;
};

#endif
