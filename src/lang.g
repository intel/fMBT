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

#include <vector>
#include <stdlib.h>
#include <string>
#include <stdio.h>

typedef struct _node {
  std::string* str;
} node;
#define D_ParseNode_User node

int action=0;
}

lang: model* ;

model: 'Model' '{' mname variables istate action* '}' {
            printf("};\n");} ;

mname: { printf("class _gen_"); } name { printf(" {\npublic:\n\t"); };

name: 'name' '=' string ';' { printf("%s",$2.str->c_str()); delete $2.str; $2.str=NULL; } ;

variables: 'variables' '{' bstr '}' { printf("//variables\n%s\n",$2.str->c_str()); } ;

istate: 'initial_state' '{' bstr '}' ;

action: 'Action' '{' { printf("\n\t//action%i: ",action); } name { printf("\n"); } guard body adapter '}' { action++; } ;

guard: 'guard' '()' '{' bstr '}' { printf("bool action%i_guard() {\n%s}\n",action,$3.str->c_str()); } ;

body: 'body' '()' '{' bstr '}' { printf("void action%i_body() {\n%s}\n",action,$3.str->c_str()); } ;

adapter: 'adapter' '()' '{' bstr '}' { printf("int action%i_adapter {\n%s}\n",action,$3.str->c_str()); } ;

bstr: "([^{}])*" { $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s); } |
        '{'bstr'}' { $$.str = new std::string(std::string("{")+*$1.str+std::string("}")); delete $1.str;
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };
