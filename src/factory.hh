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
 * creators define their own functions and use
 * <Module>Factory::Register for registration.
 */

#ifndef __factory_h__
#define __factory_h__

#include <vector>
#include <map>
#include <string>

#define FACTORY_DECLARATION(CLASSNAME)                                 \
                                                                       \
class CLASSNAME;                                                       \
class Log;                                                             \
                                                                       \
namespace CLASSNAME##Factory {                                         \
                                                                       \
    typedef CLASSNAME*(*creator)(std::vector<std::string>&,            \
                               std::string, Log& log);                 \
                                                                       \
    extern CLASSNAME* create(std::string name,                         \
                           std::vector<std::string>& actions,          \
                           std::string params, Log& log);              \
                                                                       \
    extern void add_factory(std::string name, creator c);              \
                                                                       \
    extern std::map<std::string, creator>* creators;                   \
                                                                       \
    struct Register {                                                  \
        Register(std::string name, creator c) {                        \
            add_factory(name, c);                                      \
        }                                                              \
    };                                                                 \
}


#define FACTORY_IMPLEMENTATION(CLASSNAME)                              \
std::map<std::string, CLASSNAME##Factory::creator>*                    \
    CLASSNAME##Factory::creators = 0;                                  \
                                                                       \
void CLASSNAME##Factory::add_factory(std::string name, creator c)      \
{                                                                      \
  if (!creators)                                                       \
    creators = new std::map<std::string, CLASSNAME##Factory::creator>; \
  (*creators)[name] = c;                                               \
}                                                                      \
                                                                       \
CLASSNAME* CLASSNAME##Factory::create(std::string name,                \
    std::vector<std::string>& actions,                                 \
    std::string params, Log& l)                                        \
{                                                                      \
  if (!creators) return NULL;                                          \
                                                                       \
  creator c = (*creators)[name];                                       \
                                                                       \
  if (c) {                                                             \
    return c(actions, params, l);                                      \
  }                                                                    \
                                                                       \
  return NULL;                                                         \
}

// Example:
// FACTORY_DEFAULT_CREATOR(Adapter, Adapter_dummy, "dummy")

#define FACTORY_DEFAULT_CREATOR(CLASSNAME, INSTANCENAME, ID)           \
namespace {                                                            \
  CLASSNAME* creator_func(std::vector<std::string>& actions,           \
                          std::string params, Log& l) {                \
    return new INSTANCENAME(actions, params, l);                       \
  }                                                                    \
  static CLASSNAME##Factory::Register me(ID, creator_func);            \
};

#endif
