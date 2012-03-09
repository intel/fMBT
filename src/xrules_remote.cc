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
#include "xrules_remote.hh"
#include "factory.hh"
#include "helper.hh"
#include <glib.h>

bool Xrules_remote::init()
{
  std::string& name = params;
  std::string model("remote.xrules#");
  gchar* stdout=NULL;
  gchar* stderr=NULL;
  gint   exit_status=0;
  GError *ger=NULL;
  bool ret;

  // Backward compatibility: "xrules_remote#command" should work, yet
  // "xrules_remote:command" is preferred.
  int offset = 0;
  if (name.length() > 10 && name.c_str()[model.length()-1] == '#')
      offset = model.length();

  g_spawn_command_line_sync(name.c_str()+offset,
			    &stdout,&stderr,
			    &exit_status,&ger);
  if (!stdout) {
    errormsg = std::string("xrules_remote cannot execute \"")
      + (name.c_str()+offset) + "\"";
    status = false;
    ret = false;
  } else {
    if (exit_status) {
      errormsg = std::string("xrules_remote error returned from \"")
        + (name.c_str()+offset) + "\"";
      ret=false;
    } else {
      params = model + escape_string(stdout);
      ret=Lts_xrules::init();
    }
    g_free(stdout);
    g_free(stderr);
    g_free(ger);
  }
  return ret;
}

FACTORY_DEFAULT_CREATOR(Model, Xrules_remote, "xrules_remote")
