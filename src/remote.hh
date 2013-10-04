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
#include <glib.h>
#include <string>

#include <sys/types.h>
#ifndef __MINGW32__
#include <sys/wait.h>
#endif
#include "writable.hh"

class remote {
public:
  remote():pid(0),id(0),_status(NULL) {
    g_main_context_ref(g_main_context_default());
  }
  virtual ~remote() {
    if (id) {
      while(g_main_context_iteration(NULL,FALSE));
      g_source_remove(id);
    }
    g_spawn_close_pid(pid);
    while(g_main_context_iteration(NULL,FALSE));
    g_main_context_unref(g_main_context_default());
  }
protected:
  void monitor(bool* b=NULL) {
    _status=b;
    id=g_child_watch_add(pid, watch_func,this);
  }

  static void watch_func(GPid pid,gint status,gpointer user_data) {
    remote* r;
    r=(remote*)user_data;
#ifndef __MINGW32__
    if (WIFEXITED(status)) {
      // child terminated normally
      fprintf(stderr,"%s Terminated normally (%i)\n",r->prefix.c_str(),WEXITSTATUS(status)); // The exit status.
      if (r->_status)
	*(r->_status)=false;
      return;
    }

    if (WIFSIGNALED(status)) {
      // Terminated by a signal
      fprintf(stderr,"%s Terminated by a signal (%i)\n",r->prefix.c_str(),WTERMSIG(status)); // The signal
      if (r->_status)
	*(r->_status)=false;
      return;
    }
    
    if (WCOREDUMP(status)) {
      // dumped...
      fprintf(stderr,"%s dumped the core\n",r->prefix.c_str());
      if (r->_status)
	*(r->_status)=false;
      return;
    }
#endif
    // Currently we don't care about the rest 
  }
  GPid pid;
  guint id;
  std::string prefix;
  bool* _status;
};
