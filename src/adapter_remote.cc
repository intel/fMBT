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
#define _POSIX_C_SOURCE 200809
#include "adapter_remote.hh"
#include <cstdio>
#include <glib-object.h>
#include <cstdlib>

#include <stdio.h>
#include <glib.h>
#include <fcntl.h>

#include <memory.h>

#include <sstream>
#include "helper.hh"

bool Adapter_remote::init()
{
  int _stdin,_stdout,_stderr;
  g_type_init ();
  
  gchar **argv = NULL;
  gint argc;
  GError *gerr=NULL;

  g_shell_parse_argv(prm.c_str(),&argc,&argv,&gerr);

  if (gerr) {
    errormsg = "adapter_remote: g_shell_parse_argv error: " + std::string(gerr->message)
      + " when parsing " + prm;
    log.debug(errormsg.c_str());
    status = false;
    return false;
  }

  g_spawn_async_with_pipes(NULL,argv,NULL,(GSpawnFlags)(G_SPAWN_SEARCH_PATH|G_SPAWN_DO_NOT_REAP_CHILD),NULL,NULL,&pid,&_stdin,&_stdout,&_stderr,&gerr);

  for(int i=0;i<argc;i++) {
    if (argv[i]) {
      free(argv[i]);
    }
  }
  free(argv);

  if (gerr) {
    errormsg = "adapter_remote g_spawn_async_with_pipes error: " + std::string(gerr->message);
    log.debug(errormsg.c_str());
    status = false;
    return false;
  }

  prefix="adapter remote("+prm+")";

  monitor();

  d_stdin=g_io_channel_unix_new(_stdin);  
  d_stdout=g_io_channel_unix_new(_stdout);
  d_stderr=g_io_channel_unix_new(_stderr);

  g_io_channel_set_flags(d_stderr,G_IO_FLAG_NONBLOCK,NULL);
  /*
  d_stdin=fdopen(_stdin,"w");
  d_stdout=fdopen(_stdout,"r");
  d_stderr=fdopen(_stderr,"r");
  */

  fprintf(d_stdin,"%i\n",(int)actions->size());

  for(size_t i=0;i<actions->size();i++) {
    if (urlencode) {
      char* s=g_uri_escape_string((*actions)[i].c_str(),
                                  NULL,false);

      fprintf(d_stdin,"%s\n",s);
      g_free(s);
    } else {
      fprintf(d_stdin,"%s\n",(*actions)[i].c_str());
    }

  }

  nonblock(_stdin);
  nonblock(_stdout);
  g_io_channel_flush(d_stdin,NULL);

  return true;
}

std::string Adapter_remote::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  if (!status) return errormsg;

  return t.str();
}

Adapter_remote::Adapter_remote(Log& l, std::string& params, bool encode) :
  Adapter::Adapter(l),remote(), read_buf(NULL), read_buf_pos(0),
  d_stdin(NULL), d_stdout(NULL), d_stderr(NULL),
  urlencode(encode)
{
  prm = params;
  read_buf = (char*)malloc(MAX_LINE_LENGTH+1);
  memset(read_buf, 'M', MAX_LINE_LENGTH);
}

#include <errno.h>

void Adapter_remote::execute(std::vector<int>& action)
{
  char* s = NULL;
  size_t si = 0;
  int e;

  fprintf(d_stdin, "%i\n", action[0]);

  g_io_channel_flush(d_stdin,NULL);

readagain:
  while(g_main_context_iteration(NULL,FALSE));
  if ((e=getline(&s,&si,d_stderr)) < 0) {
    static const char* m[] = { "<remote read_error=\"%i,%i,%s\"/>\n",
                               "remote read error %i, %i,%s\n"};
    log.debug("Adapter_remote::execute reading child processes execution status failed\n");
    log.error(m,e,errno,strerror(errno));
    action.resize(0);
    return;
  }
  if (strlen(s) > 0 && (s[0] == 'l' || s[0] == 'e') ) {
    // Remote log message. Protocol requires that it's already URL
    // encoded (otherwise it could not contain linebreaks and other
    // special characters worth logging) => no encoding needed when
    // rewriting it to the log.
    if (s[strlen(s)-1] == '\n') s[strlen(s)-1] = '\0';
    log.print("<remote msg=\"%s\"/>\n",(s+1));
    if (s[0] == 'e') {
      fprintf(stderr,"%s\n",unescape_string(s+1));
    }
    free(s);
    s = NULL;
    goto readagain;
  }

  if (!string2vector(log,s,action,Alphabet::ALPHABET_MIN,
		     actions->size(),this) || action.size()==0) {
    // Something wrong...
    char* escaped = escape_string(s);
    if (escaped) {
      static const char* m[] = { "<remote protocol_error=\"%s\"/>\n","%s\n"};
      log.error(m,s);
      escape_free(escaped);
    }
    action.resize(0);
  }

  std::free(s);
}

int Adapter_remote::observe(std::vector<int> &action,bool block)
{
  char* s=NULL;
  size_t si=0;

  while(g_main_context_iteration(NULL,FALSE));

  if (block) {
    while (agetline(&s,&si,d_stdout,read_buf,read_buf_pos,log)<=0) {}
  } else {
    if (agetline(&s,&si,d_stdout,read_buf,read_buf_pos,log)<=0) {
      return 0;
    }
  }

  string2vector(log,s,action,Alphabet::ALPHABET_MIN,
		actions->size(),this);
  /*
  log.debug("Adapter_remote::observe: output action number from the SUT: '%s' == %i\n",s,action);
  */
  std::free(s);
  return action.size();
}

namespace {
  Adapter* adapter_creator(Log& l, std::string params) {
    return new Adapter_remote(l, params, true);
  }

  Adapter* adapter_creator_noencode(Log& l, std::string params) {
    return new Adapter_remote(l, params, false);
  }

  static AdapterFactory::Register with_enc("remote", adapter_creator);

  static AdapterFactory::Register without_enc("remote_noencode", adapter_creator_noencode);
}
