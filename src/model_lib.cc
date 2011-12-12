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

#include "log.hh"
#include "model.hh"
#include "conf.hh"
#include "helper.hh"
#include <dlfcn.h>

namespace {
  Model* lib_creator(Log& l, std::string params) {
    Model* m;
    std::string model_name,model_param;
    std::string s(unescape_string(strdup(params.c_str())));

    Conf::split(s, model_name, model_param);

    m = ModelFactory::create(l, model_name, model_param);    

    if (!m) {
      std::string lib("lib"+model_name+".so");
      if (dlopen(lib.c_str(),RTLD_LAZY)) {
	m = ModelFactory::create(l, model_name, model_param);
      }
    }

    return m;
  }
  static ModelFactory::Register lib("lib", lib_creator);
}
