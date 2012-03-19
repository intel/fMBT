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
  : aal(l) {

  int _stdin,_stdout,_stderr;
  g_type_init ();

  gchar **argv = NULL;
  gint argc;
  GError *gerr=NULL;

  std::string errormsg;

  g_shell_parse_argv(s.c_str(),&argc,&argv,&gerr);

  if (gerr) {
    errormsg = "aal_remote: g_shell_parse_argv error: " + std::string(gerr->message)
      + " when parsing " + s;
    _log.debug(errormsg.c_str());
    ok = false;
    return;
  }

  g_spawn_async_with_pipes(NULL,argv,NULL,G_SPAWN_SEARCH_PATH,NULL,&pid,NULL,&_stdin,&_stdout,&_stderr,&gerr);

  if (gerr) {
    errormsg = "aal_remote g_spawn_async_with_pipes error: " + std::string(gerr->message);
    _log.debug(errormsg.c_str());
    ok=false;
    return;
  }

  d_stdin=fdopen(_stdin,"w");
  d_stdout=fdopen(_stdout,"r");
  d_stderr=fdopen(_stderr,"r");

  ssize_t red=getline(&read_buf,&read_buf_pos,d_stdout);

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

  fflush(d_stdin);  
}

int aal_remote::adapter_execute(int action) {
  std::fprintf(d_stdin, "a%i\n", action);
  return getint(d_stdin,d_stdout);
}

int aal_remote::model_execute(int action) {
  std::fprintf(d_stdin, "m%i\n", action);
  return getint(d_stdin,d_stdout);
}

void aal_remote::push() {
  std::fprintf(d_stdin,"mu\n");
  fflush(d_stdin);
}

void aal_remote::pop() {
  std::fprintf(d_stdin,"mo\n");
  fflush(d_stdin);
}

bool aal_remote::reset() {
  std::fprintf(d_stdin, "mr\n");
  return getint(d_stdin,d_stdout);
}

int aal_remote::getActions(int** act) {
  std::fprintf(d_stdin, "ma\n");
  return getact(act,actions,d_stdin,d_stdout);
}

int aal_remote::getprops(int** pro) {
  std::fprintf(d_stdin, "mp\n");
  return getact(pro,tags,d_stdin,d_stdout);
}

#include <cstring>
#include "helper.hh"

namespace {

  std::map<std::string,aal_remote*> storage;

  Adapter* adapter_creator(Log& l, std::string params = "") {
    std::string remotename(unescape_string(strdup(params.c_str())));
    aal_remote* al=storage[remotename];
    if (!al) {
      al=new aal_remote(l,remotename);
      if (al->ok) {
	storage[remotename]=al;
      } else {
	delete al;
	al=NULL;
      }
    }

    if (al) {
      return new Awrapper(l,params,al);
    }
    return NULL;
  }

  Model* model_creator(Log& l, std::string params) {
    std::string remotename(unescape_string(strdup(params.c_str())));
    aal_remote* al=storage[remotename];
    if (!al) {
      al=new aal_remote(l,remotename);
      if (al->ok) {
	storage[remotename]=al;
      } else {
	delete al;
	al=NULL;
      }
    }

    if (al) {
      return new Mwrapper(l,params,al);
    }
    return NULL;
  }

  static ModelFactory  ::Register Mo("aal_remote", model_creator);
  static AdapterFactory::Register Ad("aal_remote", adapter_creator);
}

#endif
