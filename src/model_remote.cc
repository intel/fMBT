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

#include "model_remote.hh"
#include <cstdio>
#include "helper.hh"

int Model_remote::getActions(int** act)
{
  std::fprintf(d_stdin, "a\n");
  return getact(act,actions,d_stdin,d_stdout);
}

int Model_remote::getIActions(int** act)
{
  std::fprintf(d_stdin, "i\n");
  return getact(act,actions,d_stdin,d_stdout);
}


int Model_remote::execute(int action)
{
  std::fprintf(d_stdin, "%i\n", action);
  return getint(d_stdin,d_stdout);
}

int Model_remote::getprops(int** pro)
{
  std::fprintf(d_stdin, "p\n");
  return getact(pro,props,d_stdin,d_stdout);
}

bool Model_remote::reset()
{
  std::fprintf(d_stdin, "r\n");
  return getint(d_stdin,d_stdout);
}

void Model_remote::push()
{
  std::fprintf(d_stdin, "u\n");
}

void Model_remote::pop()
{
  std::fprintf(d_stdin, "o\n");
}

bool Model_remote::init()
{

  int _stdin,_stdout,_stderr;
  //  g_type_init (); needed?

  gchar **argv = (gchar**)malloc(42*sizeof(gchar*));
  gint argc;
  GError *gerr=NULL;

  g_shell_parse_argv(prm.c_str(),&argc,&argv,&gerr);

  if (gerr) {
    errormsg = "Model_remote: g_shell_parse_argv error: " + std::string(gerr->message)
      + " when parsing " + prm;
    log.debug(errormsg.c_str());
    status = false;
    return false;
  }

  g_spawn_async_with_pipes(NULL,argv,NULL,G_SPAWN_SEARCH_PATH,NULL,NULL,NULL,&_stdin,&_stdout,&_stderr,&gerr);  

  if (gerr) {
    errormsg = "model_remote g_spawn_async_with_pipes error: " + std::string(gerr->message);
    log.debug(errormsg.c_str());
    status = false;
    return false;
  }

  d_stdin=fdopen(_stdin,"w");
  d_stdout=fdopen(_stdout,"r");
  d_stderr=fdopen(_stderr,"r");

  int acount=getint(d_stdin,d_stdout);;

  action_names.push_back("\"TAU");

  for(int i=0;i<acount;i++) {
    char* line=NULL;
    size_t n;
    size_t s=getdelim(&line,&n,'\n',d_stdout);
    if (!s) {
      status = false;
      return false;
    }
    if (line[s-1]=='\n') {
      line[s-1]=0;
    }
    action_names.push_back(line);
  }

  precalc_input_output();

  int prop_count=getint(d_stdin,d_stdout);

  prop_names.push_back("\"TAU");

  for(int i=0;i<prop_count;i++) {
    char* line=NULL;
    size_t n;
    size_t s=getdelim(&line,&n,'\n',d_stdout);
    if (!s) {
      status = false;
      return false;
    }
    if (line[s-1]=='\n') {
      line[s-1]=0;
    }
    prop_names.push_back(line);    
  }
  
  return true;
}

FACTORY_DEFAULT_CREATOR(Model, Model_remote, "remote")
