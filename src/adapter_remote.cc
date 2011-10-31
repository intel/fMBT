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

void nonblock(int fd)
{
  int flags = fcntl(fd, F_GETFL, 0);
  fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

/*
 * nonblock_getline reads lines from the stream. Unlike with normal
 * getline, underlying fd can be non-blocking. The function returns
 * the number of bytes copied to lineptr, or -1 on error. If full line
 * does not fit into internal read buffer (line is longer than
 * MAX_LINE_LENGTH), the contents of the buffer is returned as a
 * line.
 */
#define MAX_LINE_LENGTH (1024*16)
ssize_t Adapter_remote::nonblock_getline(char **lineptr, size_t *n, FILE *stream, const char delimiter)
{
    int fd = fileno(stream);
    for (;;) {
        /* look for line breaks in buffered string */
        char *p = (char*)memchr(read_buf, delimiter, read_buf_pos);
        /* if read buffer is full but contains no line breaks, return
           contents of the buffer */
        if (!p && read_buf_pos == MAX_LINE_LENGTH)
            p = read_buf + read_buf_pos - 1;
        if (p) {
            size_t line_length = p - read_buf + 1;
            size_t needed_space = line_length + 1; // include \0
            if (*lineptr == NULL || *n < needed_space) {
                if (*lineptr == NULL &&
                    (*lineptr = (char*)std::malloc(needed_space)) == NULL) {
                    return -1;
                } else if ((*lineptr = (char*)std::realloc(*lineptr, needed_space)) == NULL) {
                    return -1;
                }
                *n = needed_space;
            }
            memcpy(*lineptr, read_buf, line_length);
            *((*lineptr) + line_length) = '\0';
            memmove(read_buf, p + 1, read_buf_pos - (p - read_buf));
            read_buf_pos -= line_length;
            return line_length;
        }
        /* nothing found, try reading more content to the buffer */
        ssize_t bytes_read = read(fd, read_buf + read_buf_pos, 
                                  MAX_LINE_LENGTH - read_buf_pos);
        if (bytes_read == -1) { 
            return -1;
        }
        if (bytes_read == 0) {
            return 0;
        }
        read_buf_pos += bytes_read;
    }
}

bool Adapter_remote::init()
{
  int _stdin,_stdout,_stderr;
  g_type_init ();

  gchar **argv = (gchar**)malloc(42*sizeof(gchar*));
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

  g_spawn_async_with_pipes(NULL,argv,NULL,G_SPAWN_SEARCH_PATH,NULL,&pid,NULL,&_stdin,&_stdout,&_stderr,&gerr);

  if (gerr) {
    errormsg = "adapter_remote g_spawn_async_with_pipes error: " + std::string(gerr->message);
    log.debug(errormsg.c_str());
    status = false;
    return false;
  }

  d_stdin=fdopen(_stdin,"w");
  d_stdout=fdopen(_stdout,"r");
  d_stderr=fdopen(_stderr,"r");

  std::fprintf(d_stdin,"%i\n",(int)actions.size());

  for(size_t i=0;i<actions.size();i++) {
    if (urlencode) {
      char* s=g_uri_escape_string(actions[i].c_str(),
				  NULL,false);
      
      std::fprintf(d_stdin,"%s\n",s);
      g_free(s);
    } else {
      std::fprintf(d_stdin,"%s\n",actions[i].c_str());
    }
    
  }

  nonblock(_stdin);
  nonblock(_stdout);

  fflush(d_stdin);  
  return true;
}

std::string Adapter_remote::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  if (!status) return errormsg;

  return t.str();
}


Adapter_remote::Adapter_remote(std::vector<std::string>& _actions,std::string& params,Log&l, bool encode) : Adapter::Adapter(_actions,l),read_buf(NULL),read_buf_pos(0),d_stdin(NULL),d_stdout(NULL),d_stderr(NULL), urlencode(encode)
{
  prm=params;
  read_buf = (char*)malloc(MAX_LINE_LENGTH+1);
  memset(read_buf, 'M', MAX_LINE_LENGTH);
}

/* adapter can execute.. */
void Adapter_remote::execute(std::vector<int>& action)
{
  char* s=NULL;
  size_t si=0;
  std::fprintf(d_stdin,"%i\n",action[0]);

  fflush(d_stdin);

  if (getline(&s,&si,d_stderr) < 0) {
    log.debug("Adapter_remote::execute reading child processes execution status failed\n");
    action.resize(0);
    return;
  }

  string2vector(s,action);

  std::free(s);
}

ssize_t Adapter_remote::agetline(char **lineptr, size_t *n, FILE *stream)
{
  ssize_t ret;
  bool log_redirect;
  do {
    log_redirect=false;
    ret=nonblock_getline(lineptr,n,stream);
    if (ret>0) {
      if (**lineptr=='d') {
	log.debug(*lineptr+1);
	std::free(*lineptr);
	*lineptr = NULL;
	log_redirect=true;
      }
      if (**lineptr=='l') {
	char* m=g_uri_escape_string(*lineptr+1,NULL,TRUE);
	std::free(*lineptr);
        *lineptr = NULL;
	log.print("<remote msg=\"%s\">\n",m);
	g_free(m);
	log_redirect=true;
      }
    }
    
  } while (ret>0 && log_redirect);
  return ret;
}


bool Adapter_remote::readAction(std::vector<int> &action,bool block)
{
  char* s=NULL;
  size_t si=0;

  if (block) {
    while (agetline(&s,&si,d_stdout)<=0) {}
  } else {
    if (agetline(&s,&si,d_stdout)<=0) {
      return false;
    }
  }

  string2vector(s,action);
  /*
  log.debug("Adapter_remote::readAction: output action number from the SUT: '%s' == %i\n",s,action);
  */
  std::free(s);
  return true;
}

namespace {
  Adapter* adapter_creator(std::vector<std::string>& _actions,
			   std::string params,Log&l) {
    return new Adapter_remote(_actions, params, l, true);
  }

  Adapter* adapter_creator_noencode(std::vector<std::string>& _actions,
				    std::string params,Log&l) {
    return new Adapter_remote(_actions, params, l, false);
  }

  static AdapterFactory::Register with_encoding("remote", adapter_creator);

  static AdapterFactory::Register without_encoding("remote_noencode", adapter_creator_noencode);
};
