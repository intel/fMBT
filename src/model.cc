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
#include "model.hh"
#include <iostream>

std::map<std::string,Model::creator>* Model::factory = 0;

void Model::add_factory(std::string name,creator c)
{
  if (!factory) factory = new std::map<std::string,Model::creator>();
  (*factory)[name]=c;
}

Model* Model::create(Log&l,std::string name)
{
  creator c=(*factory)[name];

  //log.debug("%s(\"%s\")\n",__func__,name.c_str());

  if (c) {
    return c(l);
  }

  throw (int)42421;

  return NULL;

}
