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
#include "writable.hh"
#include <cpuid.h>

#ifndef bit_RDRND
#define bit_RDRND       (1 << 30)
#endif

Random_Intel_HW::Random_Intel_HW(const std::string& param) {
  unsigned int level,eax,ebx,ecx,edx;
  level=1;
  __cpuid(level,eax,ebx,ecx,edx);

  if (!(ecx&bit_RDRND)) {
    status=false;
    errormsg="Intel hardware random not supported";
  }

  max_val = 4294967295U;
  single=true;
}

unsigned long Random_Intel_HW::rand() {
  unsigned int ret;

  while (!__builtin_ia32_rdrand32_step(&ret));

  return ret;
}

std::string Random_Intel_HW::stringify() {
  if (status) {
    return std::string("intel");
  }

  return Random::stringify();

}

FACTORY_DEFAULT_CREATOR(Random, Random_Intel_HW, "intel")
FACTORY_DEFAULT_CREATOR(Function, Random_Intel_HWf, "intel")
