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
#include <glib.h>

bool Xrules_remote::load(std::string& name)
{
  std::string model("remote.xrules#");
  gchar* stdout=NULL;
  gchar* stderr=NULL;
  gint   exit_status=0;
  GError *ger=NULL;
  bool ret;
  g_spawn_command_line_sync(name.c_str()+model.length(),
			    &stdout,&stderr,
			    &exit_status,&ger);
  model+=stdout;
  if (exit_status) {
    ret=false;
  } else {
    ret=Lts_xrules::load(model);
  }
  g_free(stdout);
  g_free(stderr);
  g_free(ger);
  return ret;
}

namespace {
  Model* xrules_remote_creator(Log&l) {
    return new Xrules_remote(l);
  }
  static model_factory xrules_foo("xrules_remote",xrules_remote_creator);
};
