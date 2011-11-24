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
#include "aalang.hh"
#include "aalang_cpp.hh"

aalang* obj=NULL;

typedef struct _node {
  std::string* str;
} node;
#define D_ParseNode_User node
std::vector<std::string> aname;
std::string* nstr=NULL;
}

lang: model* ;

model: 'model' namestr '{' language { obj->set_namestr(nstr); } variables istate action* '}' {  
            printf("%s",obj->stringify().c_str());
      };
language: 'language:' 'C++' ';' { obj=new aalang_cpp ; } ;

namestr: unquoted_string {
            nstr=$0.str; // I'm too lazy to figure out why this can't be returned in $0
        };

name: 'name' ':' string ';' { obj->set_name($2.str); };

variables: 'variables' '{' bstr '}' { obj->set_variables($2.str); };

istate: 'initial_state' '{' bstr '}' { obj->set_istate($2.str); } ;

action: 'action' '{' name guard body adapter '}' { obj->next_action(); };

guard: 'guard' '()' '{' bstr '}' { obj->set_guard($3.str); };

body: 'body' '()' '{' bstr '}' { obj->set_body($3.str); };

adapter: 'adapter' '()' '{' bstr '}' { obj->set_adapter($3.str); }|;

bstr: "([^{}])*" { $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s); } |
        '{'bstr'}' { $$.str = new std::string(std::string("{")+*$1.str+std::string("}")); delete $1.str;
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

unquoted_string: "([a-zA-Z]*)" { $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s); };
