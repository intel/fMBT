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
#include "coverage_market.hh"
typedef struct _node {
  char type;
  std::string* str;
  Coverage_Market::unit* u;
} cnode;
#define D_ParseNode_User cnode

Coverage_Market* cobj;

}

begin: expr { cobj->add_unit($0.u); };

expr: node             { $$.u = $0.u; }
    | node "and" expr  { $$.u = new Coverage_Market::unit_and ($0.u,$2.u); }
    | node "or" expr   { $$.u = new Coverage_Market::unit_or  ($0.u,$2.u); }
    | node "then" expr { $$.u = new Coverage_Market::unit_then($0.u,$2.u); };

node: actionname       { $$.u = cobj->req_rx_action(0,$0.str->c_str()); delete $0.str; $0.str=NULL; } 
    | 'a' actionname   { $$.type='a'; $$.u = cobj->req_rx_action($$.type,$1.str->c_str()); delete $0.str; $0.str=NULL; } 
    | 'e' actionname   { $$.type='e'; $$.u = cobj->req_rx_action($$.type,$1.str->c_str()); delete $0.str; $0.str=NULL; } 
    | '(' expr ')'     { $$.u = $1.u; } 
    | "not" node       { $$.u = new Coverage_Market::unit_not($1.u); } ;

actionname: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); $$.type=0; };
