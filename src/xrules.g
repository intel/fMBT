{
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
#include <stdlib.h>
#include <string>
typedef struct _node {
  unsigned int val;
  std::string* str;
} node;
#define D_ParseNode_User node
#include "lts_xrules.hh"
Lts_xrules* xobj;

}

xrules_file: filename+ rule+;

filename: int '=' string { xobj->add_file($0.val,*$2.str); delete $2.str; $2.str=NULL; };

rule: | component+ '->' string { xobj->add_result_action($2.str); };

component: '(' int ',' string ')' { xobj->add_component($1.val,*$3.str); delete $3.str; $3.str=NULL; };

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

int: istr { $$.val = atoi($n0.start_loc.s); };

istr: "[0-9]+";
