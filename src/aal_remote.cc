/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012 Intel Corporation.
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

#include "config.h"
#ifndef DROID
#include "aal_remote.hh"
#include <glib-object.h>
#include <glib.h>
#include "helper.hh"

aal_remote::aal_remote(Log&l,std::string& s)
  : aal(l,s), read_buf(NULL), read_buf_pos(0),
    d_stdin(NULL), d_stdout(NULL), d_stderr(NULL)
{

  int _stdin=-1,_stdout=-1,_stderr=-1;
  gchar **argv = NULL;
  gint argc=0;
  GError *gerr=NULL;


  g_shell_parse_argv(s.c_str(),&argc,&argv,&gerr);

  if (gerr) {
    errormsg = "aal_remote: g_shell_parse_argv error: " + std::string(gerr->message)
      + " when parsing " + s;
    _log.debug(errormsg.c_str());
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
    errormsg = "aal_remote: g_spawn_async_with_pipes error: " + std::string(gerr->message);
    _log.debug(errormsg.c_str());
    status = false;
    return;
  }

  nonblock(_stderr);

  monitor(&status);

  prefix="aal remote("+s+")";

  d_stdin=fdopen(_stdin,"w");
  d_stdout=fdopen(_stdout,"r");
  d_stderr=fdopen(_stderr,"r");

  ssize_t red=bgetline(&read_buf,&read_buf_pos,d_stdout,l);

  action_names.push_back("TAU");

  while (red>1) {
    read_buf[red-1]='\0'; // no not include linefeed
    action_names.push_back(read_buf);
    red=getline(&read_buf,&read_buf_pos,d_stdout);
  }

  red=getline(&read_buf,&read_buf_pos,d_stdout);

  tag_names.push_back("TAU");

  while (red>1) {
    read_buf[red-1]='\0'; // no not include linefeed
    tag_names.push_back(read_buf);
    red=getline(&read_buf,&read_buf_pos,d_stdout);
  }

  free(read_buf);
  read_buf_pos=0;

  fflush(d_stdin);
}

void aal_remote::handle_stderr() {
  char* line=NULL;
  size_t n=0;
  char* read_buf=NULL;
  size_t read_buf_pos=0;

  if (agetline(&line,&n,d_stderr,read_buf,read_buf_pos,_log) && line) {
    fprintf(stderr,"%s\n",line);
    free(read_buf);
  }
}

int aal_remote::adapter_execute(int action,const char* params) {
  while(g_main_context_iteration(NULL,FALSE));

  if (!status) {
    return 0;
  }

  if (params)
    std::fprintf(d_stdin, "ap%s\n",params);

  std::fprintf(d_stdin, "a%i\n", action);
  return getint(d_stdin,d_stdout,_log);
}

int aal_remote::model_execute(int action) {
  while(g_main_context_iteration(NULL,FALSE));

  if (!status) {
    return 0;
  }

  handle_stderr();

  std::fprintf(d_stdin, "m%i\n", action);
  return getint(d_stdin,d_stdout,_log);
}

void aal_remote::push() {
  while(g_main_context_iteration(NULL,FALSE));
  if (status) {
    handle_stderr();
    std::fprintf(d_stdin,"mu\n");
    fflush(d_stdin);
  }
}

void aal_remote::pop() {
  while(g_main_context_iteration(NULL,FALSE));
  if (status) {
    handle_stderr();
    std::fprintf(d_stdin,"mo\n");
    fflush(d_stdin);
  }
}

bool aal_remote::reset() {
  handle_stderr();
  std::fprintf(d_stdin, "mr\n");
  bool rv = (getint(d_stdin,d_stdout,_log) == 1);
  if (!rv) {
    errormsg = "aal_remote model failed to reset \"" + params + "\".\n"
      "      (try executing: echo mr | " + params + ")";
    status = false;
  }
  return rv;
}

bool aal_remote::init() {
  std::fprintf(d_stdin, "ai\n");
  bool rv = (getint(d_stdin,d_stdout,_log) == 1);
  if (!rv) {
    errormsg = "aal_remote adapter failed to init \"" + params + "\".\n"
      "      (try executing: echo ai | " + params + ")";
    status = false;
  }
  return rv;
}

int aal_remote::getActions(int** act) {
  while(g_main_context_iteration(NULL,FALSE));

  if (!status) {
    return 0;
  }

  handle_stderr();

  std::fprintf(d_stdin, "ma\n");
  return getact(act,actions,d_stdin,d_stdout,_log);
}

int aal_remote::getprops(int** pro) {
  while(g_main_context_iteration(NULL,FALSE));

  if (!status) {
    return 0;
  }

  handle_stderr();

  std::fprintf(d_stdin, "mp\n");
  return getact(pro,tags,d_stdin,d_stdout,_log);
}

int aal_remote::observe(std::vector<int> &action, bool block)
{
  while(g_main_context_iteration(NULL,FALSE));

  if (!status) {
    action.clear();
    action.push_back(Alphabet::SILENCE);
    return true;
  }

  handle_stderr();

  if (block) {
    std::fprintf(d_stdin, "aob\n"); // block
  } else {
    std::fprintf(d_stdin, "aop\n"); // poll
  }
  int action_alternatives = getact(NULL, action, d_stdin, d_stdout,_log);

  if (action_alternatives > 0) {
    if (action[0] == Alphabet::SILENCE) {
      action.clear();
      return Alphabet::SILENCE;
    }
  }
  return action_alternatives != 0;
}

#include <cstring>
#include "helper.hh"

namespace {
  aal* al_helper(Log& l, std::string params) {
    std::string remotename(params);
    unescape_string(remotename);
    std::string fullname("aal_remote("+remotename+")");

    if (aal::storage==NULL) {
      aal::storage=new std::map<std::string,aal*>;
    }

    aal* al=(*aal::storage)[fullname];
    if (!al) {
      al=new aal_remote(l,remotename);
      (*aal::storage)[fullname]=al;
    }
    return al;
  }

  Adapter* adapter_creator(Log& l, std::string params = "") {
    aal* al=al_helper(l,params);

    if (al) {
      return new Awrapper(l,params,al);
    }
    return NULL;
  }

  Model* model_creator(Log& l, std::string params) {
    aal* al=al_helper(l,params);

    if (al) {
      return new Mwrapper(l,params,al);
    }
    return NULL;
  }

  static ModelFactory  ::Register Mo("aal_remote", model_creator);
  static AdapterFactory::Register Ad("aal_remote", adapter_creator);
}

#endif
