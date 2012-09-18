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
#ifndef __alphabet_impl_hh__
#define __alphabet_impl_hh__

#include "alphabet.hh"
#include <string>
#include <vector>

class Alphabet_impl: public Alphabet {
public:
  Alphabet_impl(std::vector<std::string>& _ActionNames,
		std::vector<std::string>& _SPNames):
    ActionNames(_ActionNames),SPNames(_SPNames) {}

  virtual ~Alphabet_impl() {}
  //! Returns names of all actions available.
  virtual std::vector<std::string>& getActionNames() {
    return ActionNames;
  }

  //! Returns names of all available state propositions
  virtual std::vector<std::string>& getSPNames() {
    return SPNames;
  }

  //! Returns the name of the given action
  virtual std::string& getActionName(int action) {
    return ActionNames[action];
  }

  std::vector<std::string>& ActionNames;
  std::vector<std::string>& SPNames;
};

#endif
