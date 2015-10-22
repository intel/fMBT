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

/* 
 * This file defines macros that declare and implement factories for
 * pluggable fMBT modules, such as adapters, heuristics and coverages.
 *
 * Every module registers its name with a creator function pointer to
 * <Module>Factory::creators. Registered modules are instantiated by
 * calling <Module>Factory::create(name, ...) that calls associated
 * creator function. Yet FACTORY_DEFAULT_CREATOR provides a default
 * creator function, modules that need to do something special in
 * creators can define their own functions and use
 * <Module>Factory::Register for registering it.
 *
 * FACTORY_DECLARATION(Module) is needed in the header file of the
 * Module base class only.
 *
 * FACTORY_IMPLEMENTATION(Module) is needed in the implementation of
 * the Module base class only.
 *
 * FACTORY_DEFAULT_CREATOR(Module, Class, Name) is needed in
 * the implementation of every Class that implements Module.
 */

#ifndef __factory_h__
#define __factory_h__

#include <vector>
#include <map>
#include <string>
#include <stdlib.h>

#ifndef FACTORY_CREATE_PARAMS
#define FACTORY_CREATE_PARAMS Log& log,                                \
                       std::string name,                               \
                       std::string params
#endif

#ifndef FACTORY_CREATE_DEFAULT_PARAMS
#define FACTORY_CREATE_DEFAULT_PARAMS = ""
#endif

#ifndef FACTORY_CREATOR_PARAMS
#define FACTORY_CREATOR_PARAMS Log& log, std::string params
#define FACTORY_CREATOR_PARAMS2 log, params
#endif

#undef FACTORY_DECLARATION
#undef FACTORY_IMPLEMENTATION
#undef FACTORY_DEFAULT_CREATOR

#define FACTORY_DECLARATION(MODULETYPE)                                \
                                                                       \
class MODULETYPE;                                                      \
                                                                       \
namespace MODULETYPE##Factory {                                        \
                                                                       \
    typedef MODULETYPE*(*creator)(FACTORY_CREATOR_PARAMS,void*);       \
                                                                       \
    extern MODULETYPE* create(FACTORY_CREATE_PARAMS);                  \
                                                                       \
    extern void add_factory(std::string name, creator c,void* p);      \
                                                                       \
    extern void remove_factory(std::string name);                      \
                                                                       \
    extern std::map<std::string, std::pair<creator, void*> >* creators;\
                                                                       \
    struct Register {                                                  \
      Register(std::string _name, creator c,void* p=NULL):name(_name) {\
	  add_factory(name, c, p);				       \
        }                                                              \
        ~Register() {						       \
	    remove_factory(name);				       \
        }                                                              \
	std::string name;                                              \
    };                                                                 \
}

#define FACTORY_CREATORS(MODULETYPE)                                   \
  std::map<std::string, std::pair<MODULETYPE##Factory::creator,void*> >*\
    MODULETYPE##Factory::creators = 0;                                 

#define FACTORY_ADD_FACTORY(MODULETYPE)                                \
void MODULETYPE##Factory::add_factory(std::string name, creator c,void* p=NULL) \
{                                                                      \
  if (!creators) {                                                     \
    creators = new std::map<std::string, std::pair<MODULETYPE##Factory::creator, void*> >; \
  }                                                                    \
  (*creators)[name] = std::pair<MODULETYPE##Factory::creator, void*>(c,p); \
}                                                                      \
                                                                       \
void MODULETYPE##Factory::remove_factory(std::string name)             \
{                                                                      \
  if (creators) {                                                      \
    creators->erase(name);                                             \
    if (creators->empty()) {                                           \
      delete creators;                                                 \
      creators = NULL;                                                 \
    }                                                                  \
  }                                                                    \
}


#define FACTORY_CREATE(MODULETYPE)                                     \
MODULETYPE* MODULETYPE##Factory::create(                               \
    FACTORY_CREATE_PARAMS FACTORY_CREATE_DEFAULT_PARAMS)               \
{                                                                      \
  if (!creators) return NULL;                                          \
                                                                       \
  std::map<std::string, std::pair<creator,void*> >::iterator i = (*creators).find(name); \
                                                                       \
  if (i!=creators->end()) return (i->second.first)(FACTORY_CREATOR_PARAMS2,i->second.second); \
                                                                       \
  return NULL;                                                         \
}

#define FACTORY_IMPLEMENTATION(MODULETYPE)                             \
FACTORY_CREATORS(MODULETYPE)                                           \
FACTORY_ADD_FACTORY(MODULETYPE)                                        \
FACTORY_CREATE(MODULETYPE)

#define CONCAT2(x, y)     x ## y
#define CONCAT(x, y)      CONCAT2(x, y)
#define UNIQUENAME(prefix) CONCAT(prefix, __LINE__)

#define FACTORY_DEFAULT_CREATOR(MODULETYPE, CLASSNAME, ID)	       \
namespace {                                                            \
  MODULETYPE* UNIQUENAME(creator_func) (FACTORY_CREATOR_PARAMS FACTORY_CREATE_DEFAULT_PARAMS, void* p=NULL) \
  {                                                                    \
    return new CLASSNAME(FACTORY_CREATOR_PARAMS2);		       \
  }                                                                    \
  static MODULETYPE##Factory::Register UNIQUENAME(me)(ID, UNIQUENAME(creator_func)); \
}

#endif

