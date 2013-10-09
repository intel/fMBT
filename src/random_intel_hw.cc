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

#define _RANDOM_INTERNAL_
#include "random_intel_hw.hh"

Random_Intel_HW::Random_Intel_HW(const std::string& param) {
  max_val = 4294967295U;
}

unsigned long Random_Intel_HW::rand() {
  unsigned int ret;

  while (!__builtin_ia32_rdrand32_step(&ret)) {}

  return ret;
}

FACTORY_DEFAULT_CREATOR(Random, Random_Intel_HW, "intel")
FACTORY_DEFAULT_CREATOR(Function, Random_Intel_HW, "intel")
