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
  Coverage_Market::unit_tag* tag;
  int i;
} cnode;
#define D_ParseNode_User cnode
Coverage_Market* cobj;

#include "d/d.h"
#include "helper.hh"

extern D_ParserTables parser_tables_covlang;

Coverage_Market::unit* tagspec_helper(Coverage_Market::unit_tag* l,Coverage_Market::unit* c,
                                      Coverage_Market::unit_tag* r) {
    if (l || r) {
        if (!l) {
            l=new Coverage_Market::unit_tag();
            l->value.first=0;
            l->value.second=0;
        }

        if (!r) {
            r=new Coverage_Market::unit_tag();
            r->value.first=0;
            r->value.second=0;
        }
        return new Coverage_Market::unit_tagunit(l,c,r);
    }
    return c;
}


Coverage_Market::unit* inthelper(Coverage_Market::unit* u,
                                 int count) {
    Coverage_Market::unit_leaf* ul = 
        dynamic_cast<Coverage_Market::unit_leaf*>(u);

    if (ul) {
        ul->value.second*=count;
        return u;
    }

    Coverage_Market::unit_mult* um=
        dynamic_cast<Coverage_Market::unit_mult*>(u);

    if (um) {
        um->max*=count;
        return u;
    }

    return new Coverage_Market::unit_mult(u,count);
}

}

begin: expr { cobj->add_unit($0.u); };

expr: node             { $$.u = $0.u; }
    | node "and" expr  { $$.u = new Coverage_Market::unit_and ($0.u,$2.u); }
    | node "or" expr   { $$.u = new Coverage_Market::unit_or  ($0.u,$2.u); }
    | node "then" expr { $$.u = new Coverage_Market::unit_then_($0.u,$2.u); } ;

node: tag_spec actionname tag_spec  { $$.type='e'; $$.u = cobj->req_rx_action($$.type,*$1.str,$0.tag,$2.tag); delete $1.str; $1.str=NULL; }
    | ('a' | 'A' | 'all' ) actionname   { $$.type='a'; $$.u = cobj->req_rx_action($$.type,*$1.str); delete $1.str; $1.str=NULL; }
    | ('e' | 'E' | 'any' ) actionname   { $$.type='e'; $$.u = cobj->req_rx_action($$.type,*$1.str); delete $1.str; $1.str=NULL; }
    | tag_spec '(' expr ')'  tag_spec   { $$.u = tagspec_helper($0.tag,$2.u,$4.tag); }
    | "not" node       { $$.u = new Coverage_Market::unit_not($1.u); } 
    | uint '*' node    { $$.u = inthelper($2.u,$0.i); }
    | node '*' uint    { $$.u = inthelper($0.u,$2.i); }
    | 'uwalks' '(' expr ')' { $$.u = new Coverage_Market::unit_walk($2.u,true); }
    | 'eageruwalks' '(' expr ')' { $$.u = new Coverage_Market::unit_walk($2.u,false); }
    | 'perm' '(' uint ')' { $$.u = new Coverage_Market::unit_perm($2.i,cobj); }
    | 'file' '(' name ')' [
            char* ss=strndup($n2.start_loc.s+1, $n2.end-$n2.start_loc.s-2);
            char* bb=readfile(ss);
            if (bb==NULL) {
                free(ss);
                ${reject};
            } else {
                D_Parser *p = new_D_Parser(&parser_tables_covlang, 32);
                p->start_state = D_START_STATE_expr;
                p->loc.pathname=ss;
                p->save_parse_tree=1;
                D_ParseNode* ret=dparse(p,bb,strlen(bb));
                free(ss);
                free(bb);
                if (ret) {
                    $$.u = ret->user.u;
                    free_D_ParseNode(p, ret);
                    free_D_Parser(p);
                } else {
                    free_D_Parser(p);
                    ${reject};
                }
             }
        ]
    ;

tagname: name { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;

actionname: name { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;

tag_spec: '[' tag_expr ']' { 
            $$.tag = $1.tag;
            //$$.str = new std::string($n1.start_loc.s+1,$n1.end-$n1.start_loc.s-2);
        } |
        {
            $$.tag = NULL;
            //$$.str = new std::string("");
        }
    ;

tag_node: tagname      { $$.tag = cobj->req_rx_tag(*$0.str); delete $0.str; }
    | '(' tag_expr ')' { $$.tag = $1.tag; }
    | "not" tag_node   { $$.tag = new Coverage_Market::unit_tagnot($1.tag); }
    ;

tag_expr: tag_node { $$.tag = $0.tag; }
          | tag_node 'and' tag_expr { $$.tag=new Coverage_Market::unit_tagand($0.tag,$2.tag); }
          | tag_node 'or'  tag_expr { $$.tag=new Coverage_Market::unit_tagor ($0.tag,$2.tag); }
          ;



name: "\"([^\"\\]|\\[^])*\"" |  "\'([^\'\\]|\\[^])*\'";

uint: istr { $$.i = atoi($n0.start_loc.s); };

istr: "[0-9]+";
