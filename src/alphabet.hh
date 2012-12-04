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
#ifndef __alphabet_hh__
#define __alphabet_hh__

#include <string>

class Alphabet {
public:
enum values {
  OUTPUT_ONLY =-1,
  DEADLOCK = -2,
  SILENCE = -3,
  TIMEOUT = -4,
  ERROR   = -5,
  ALPHABET_MIN = ERROR
};

  virtual ~Alphabet() {}
  //! Returns names of all actions available.
  virtual std::vector<std::string>& getActionNames() = 0;

  //! Returns names of all available state propositions
  virtual std::vector<std::string>& getSPNames()     = 0;

  //! Returns the name of the given action
  virtual std::string& getActionName(int action)     = 0;
  
};

#endif
