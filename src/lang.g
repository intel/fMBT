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
#include "aalang_java.hh"
#include "aalang_py.hh"

std::string result("");
aalang* obj=NULL;

typedef struct _node {
  std::string* str;
} node;
#define D_ParseNode_User node
std::vector<std::string> aname;

bool adapter,body,guard;

int count=1;

char *ops;
void *ops_cache=&count;

#include "d.h"

void raise_error(d_loc_t& sl,Parser *p) {
    p->last_syntax_error_line = sl.line;
    p->user.syntax_errors++;
    p->user.loc.line= sl.line;
    p->user.loc.ws = sl.s-1;
    p->user.syntax_error_fn((D_Parser*)p);
}

int bstr_scan(char *ops, void *ops_cache, d_loc_t *loc,
              unsigned char *op_assoc, int *op_priority)
{
    int count=1;
    int pos=0;
//    printf("%i %i (%s)\n",loc->line,loc->col,loc->s);
    while (count) {
        switch (loc->s[pos]) {
        case '\n':
            pos++;
            loc->line++;
            loc->col=0;
            break;
        case '{':
            loc->col++;
            count++;
            pos++;
            break;
        case '}':
            loc->col++;
            count--;
            if (count) pos++;
            break;
        default:
            loc->col++;
            pos++;
        }
    }

    loc->s+=pos;
    loc->ws=loc->s;
    return 1;
}
}

aal: comment* aal_start header+ ( ( act | tag) (act | tag | comment )* )? '}' comment* ;

aal_start: 'aal' string '{' language {
            obj->set_namestr($1.str);
        } ;

header: variables | ainit | istate | push | pop | comment;

comment: '#' "[^\n]*" { } ;


act: 'action' astr { guard=false;body=false;adapter=false; } '{' ab '}' {
            if (!guard) {
                obj->empty_guard();
            }
            if (!body) {
                obj->empty_body();
            }
            if (!adapter) {
                obj->empty_adapter();
            }
            obj->next_action();
        };

ab: (comment|guard|body|adapter)*;

astr:   string          {
            obj->set_name($0.str);
        } |
        astr ',' string {
            obj->set_name($2.str);
        } ;

tag_content: (comment|guard|adapter)*;

tag: 'tag' tstr { guard=false;body=true;adapter=false; } '{' tag_content '}' {
      if (!guard) {
        obj->empty_guard();
      }
      if (!adapter) {
        obj->empty_adapter();
      }
      obj->next_tag();
    };

tstr:   string          {
            obj->set_tagname($0.str);
        } |
        tstr ',' string {
            obj->set_tagname($2.str);
        } ;

push: 'push' '{' bstr '}' {
            obj->set_push($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col);
        } ;

pop:  'pop' '{' bstr '}' {
            obj->set_pop ($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

language: 'language:' cpp    { obj=new aalang_cpp  ; } starter ';'? |
          'language:' java   { obj=new aalang_java ; } starter ';'? |
          'language:' python { obj=new aalang_py   ; } starter ';'? ;

cpp: 'C++' | 'cpp' | 'c++';

java: 'oak' | 'green' | 'java';

starter: |
        '{' bstr '}' {
            obj->set_starter($1.str,$n1.start_loc.pathname,$n1.start_loc.line,$n1.start_loc.col); };

python: 'Python' | 'python' | 'py';

variables: 'variables' '{' bstr '}' {
            obj->set_variables($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); };

istate: 'initial_state' '{' bstr '}' {
            obj->set_istate($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

ainit: 'adapter_init' '{' bstr '}' {
            obj->set_ainit($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

guard: 'guard' '()' '{' bstr '}' {
            if (guard) {
                raise_error($n0.start_loc,(Parser*)_parser);
            } else {
                obj->set_guard($3.str,$n3.start_loc.pathname,$n3.start_loc.line,$n3.start_loc.col); guard=true;
            }
        } ;
body: ('body'|'model') '()' '{' bstr '}' { if (body) {
                raise_error($n0.start_loc,(Parser*)_parser);
            } else {
                obj->set_body($3.str,$n3.start_loc.pathname,$n3.start_loc.line,$n3.start_loc.col);
                body=true;
            }
        } ;

adapter: 'adapter' '()' '{' bstr '}' { if (adapter) {
                raise_error($n0.start_loc,(Parser*)_parser);
            } else {
                obj->set_adapter($3.str,$n3.start_loc.pathname,$n3.start_loc.line,$n3.start_loc.col);
                adapter=true;
            }
        };

bstr: (${scan bstr_scan(ops,ops_cache)})* {
            char* start=d_ws_before(NULL,& $n0);
            char* end=d_ws_after(NULL,& $n0);
            $$.str = new std::string(start,end-start);
            } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2);
        };
