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
#include "lts_remote.hh"
#include "factory.hh"
#include "helper.hh"
#include <glib.h>

bool Lts_remote::init()
{
  std::string &name = params;
  std::string model("remote.lts#");
  gchar* __stdout=NULL;
  gint   exit_status=0;
  GError *ger=NULL;
  bool ret;

  // Backward compatibility: make lts_remote#command work,
  // yet now lts_remote:command is preferred.
  int offset = 0;
  if (name.length() > 10 && name.c_str()[10] == '#') offset = 11;

  g_spawn_command_line_sync(name.c_str() + offset,&__stdout,NULL,
			    &exit_status,&ger);
  if (!__stdout) {
    errormsg = std::string("Lts_remote cannot execute \"") + (name.c_str()+offset) + "\"";
    status = false;
    ret = false;
  } else {
    if (exit_status) {
      errormsg = std::string("lts_remote error returned from \"")
        + (name.c_str()+offset) + "\"";
      ret=false;
    } else {
      char*escaped=escape_string(__stdout);
      params = model + escaped;
      escape_free(escaped);
      ret=Lts::init();
    }
  }

  if (__stdout) {
    g_free(__stdout);
  }

  if (ger) {
    g_error_free(ger);
  }

  return ret;
}

namespace _lts_remote_1 { FACTORY_DEFAULT_CREATOR(Model, Lts_remote, "lts_remote") }
namespace _lts_remote_2 { FACTORY_DEFAULT_CREATOR(Model, Lts_remote, "lsts_remote") }
