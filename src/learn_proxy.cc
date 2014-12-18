/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "learn_proxy.hh"

Learn_proxy::Learn_proxy(Log&l): Learning(l), lt(NULL),la(NULL) {}

void Learn_proxy::suggest(int action) {
  if (lt)
    lt->suggest(action);
  if (la)
    la->suggest(action);
}

void Learn_proxy::execute(int action) {
  if (lt)
    lt->execute(action);
  if (la)
    la->execute(action);
}

float Learn_proxy::getE(int action) {
  if (lt)
    return lt->getE(action);

  return Learning::getE(action);
}

float Learn_proxy::getF(int action) {
  if (la)
    return la->getF(action);

  return Learning::getF(action);
}


float Learn_proxy::getC(int sug,int exe) {
  if (la)
    return la->getC(sug,exe);

  return Learning::getC(sug,exe);
}

void Learn_proxy::setAlphabet(Alphabet* a) {
  Learning::setAlphabet(a);
  if (lt)
    lt->setAlphabet(a);
  if (la)
    la->setAlphabet(a);
}

