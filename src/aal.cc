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

#include "aal.hh"
#include "helper.hh"
#include <cstdlib>
#include <glib/gprintf.h>

std::map<std::string,aal*>* aal::storage=NULL;

int aal::input(const std::string& s) {
  return action("i:"+s);
}

int aal::output(const std::string& s) {
  return action("o:"+s);
}


int aal::action(const std::string& s)
{
  static std::map<std::string,int> amap;

  if (amap.empty()) {
    for(unsigned i=0;i<action_names.size();i++) {
      amap[action_names[i]]=i;
    }
  }
  return amap[s];
}

void aal::log(const char* format, ...)
{
  va_list ap;
  char* pre_msg=NULL;

  va_start(ap, format);
  if (g_vasprintf(&pre_msg,format,ap)>0) {
    char* msg=escape_string(pre_msg);
    _log.print("<aal type=\"user\" msg=\"%s\">\n",msg);
    std::free(pre_msg);
    escape_free(msg);
  }

  va_end(ap);
}

namespace {
  aal* al_helper() {

    if (aal::storage==NULL) {
      return NULL;
    }

    if (aal::storage->empty() || aal::storage->size()!=1) {
      return NULL;
    }
    return aal::storage->begin()->second;
  }

  Adapter* adapter_creator(Log& l,std::string params,void*) {
    aal* al=al_helper();

    if (al) {
      return new Awrapper(l,params,al);
    }
    return NULL;
  }

  Model* model_creator(Log& l,std::string params,void*) {
    aal* al=al_helper();

    if (al) {
      return new Mwrapper(l,params,al);
    }
    return NULL;
  }

  static ModelFactory  ::Register Mo("aal", model_creator);
  static AdapterFactory::Register Ad("aal", adapter_creator);
}
