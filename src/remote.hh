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
#include <sys/wait.h>

class remote {
public:
  remote():pid(0),id(0) {}
  virtual ~remote() {
    if (id) 
      g_source_remove(id);
  }
protected:
  void monitor() {
    id=g_child_watch_add(pid, watch_func,this);
  }

  static void watch_func(GPid pid,gint status,gpointer user_data) {
    remote* r;
    r=(remote*)user_data;

    if (WIFEXITED(status)) {
      // child terminated normally
      fprintf(stderr,"%s Terminated normally (%i)\n",r->prefix.c_str(),WEXITSTATUS(status)); // The exit status.
      return;
    }

    if (WIFSIGNALED(status)) {
      // Terminated by a signal
      fprintf(stderr,"%s Terminated by a signal (%i)\n",r->prefix.c_str(),WTERMSIG(status)); // The signal
      return;
    }
    
    if (WCOREDUMP(status)) {
      // dumped...
      fprintf(stderr,"%s dumped the core\n",r->prefix.c_str());
      return;
    }
    // Currently we don't care about the rest 
  }
  GPid pid;
  guint id;
  std::string prefix;
};
