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

std::string result("");

typedef struct _node {
  std::string* str;
} node;
#ifdef D_ParseNode_User
#undef D_ParseNode_User
#endif
#define D_ParseNode_User node

#include "aalang.hh"
#include "aalang_cpp.hh"
#include "aalang_java.hh"
#include "aalang_py.hh"
aalang* obj=NULL;

std::vector<std::string> aname;

bool adapter,body,guard;
#include <stack>

std::stack<bool> abg_stack;
int count=1;

char *ops;
void *ops_cache=&count;

#include "d.h"

static std::pair<std::string,std::pair<std::string,int> > pa;

static void name_syntax_error_report(struct D_Parser *ap) {
    Parser *p = (Parser *)ap;

    char *fn = d_dup_pathname_str(p->user.loc.pathname);

    fprintf(stderr,"%s:%d: name error '%s' already defined at %s:%d\n",
                    fn,p->user.loc.line,pa.first.c_str(),
                    pa.second.first.c_str(),
                    pa.second.second);

    FREE(fn);
}

void raise_error(d_loc_t& sl,Parser *p) {
    p->last_syntax_error_line = sl.line;
    p->user.syntax_errors++;
    p->user.loc.line= sl.line;
    p->user.loc.ws = sl.s-1;
    p->user.syntax_error_fn((D_Parser*)p);
}

void raise_name_error(d_loc_t& sl,Parser *p,std::string* name) {
    pa.first=*name;
    pa.second=obj->get_namepos(name);
    p->user.syntax_error_fn=name_syntax_error_report;
    raise_error(sl,p);
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

aal: comment* aal_start header+ ( ( act | tag | parser ) (act | tag | parser | header )* )? '}' comment* ;

aal_start: 'aal' string '{' language {
            obj->set_namestr($1.str);
        } ;

header: variables | ainit | aexit | istate | push | pop | comment ;

comment: '#' "[^\n]*" { } ;

params: | '(' paramlist ')' ;

paramlist: string | paramlist ',' string ;

parser: parallel params | serial params ;

serial_start: 'serial' { obj->serial(true); } ;
parallel_start: 'parallel' { obj->parallel(true); } ;

spinc: (comment)* ( act | tag | parser ) ( act | tag | parser | header )* ;

serial: serial_start '{' spinc '}'
        { obj->serial(false); } ;

parallel: parallel_start '{' spinc '}'
        { obj->parallel(false); } ;

act: ( 'action' astr | 'input' istr | 'output' ostr ) {
            abg_stack.push(guard);
            abg_stack.push(body);
            abg_stack.push(adapter);
            guard=false;body=false;adapter=false; } '{' ab '}' {
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
            adapter=abg_stack.top();abg_stack.pop();
            body=abg_stack.top();abg_stack.pop();
            guard=abg_stack.top();abg_stack.pop();
        } ;

ab: (header|guard|body|adapter|tag|act|parser)*;

astr:   string          {
            if (obj->check_name($0.str,$n0.start_loc.pathname,$n0.start_loc.line)) {
                raise_name_error($n0.start_loc,(Parser*)_parser,$0.str);
            }
            obj->set_name($0.str,true);
        } |
        astr ',' string {
            if (obj->check_name($2.str,$n2.start_loc.pathname,$n2.start_loc.line)) {
                raise_name_error($n2.start_loc,(Parser*)_parser,$2.str);
            }
            obj->set_name($2.str);
        } ;

istr:   string          {
            std::string* tmp=new std::string("i:" + *$0.str);
            delete $0.str;
            if (obj->check_name(tmp,$n0.start_loc.pathname,$n0.start_loc.line)) {
                raise_name_error($n0.start_loc,(Parser*)_parser,tmp);
            }
            obj->set_name(tmp,true,aalang::IACT);
        } |
        istr ',' string {
            std::string* tmp=new std::string("i:" + *$2.str);
            delete $2.str;
            if (obj->check_name(tmp,$n2.start_loc.pathname,$n2.start_loc.line)) {
                raise_name_error($n2.start_loc,(Parser*)_parser,tmp);
            }
            obj->set_name(tmp,false,aalang::IACT);
        } ;

ostr:   string          {
            std::string* tmp=new std::string("o:" + *$0.str);
            delete $0.str;
            if (obj->check_name(tmp,$n0.start_loc.pathname,$n0.start_loc.line)) {
                raise_name_error($n0.start_loc,(Parser*)_parser,tmp);
            }
            obj->set_name(tmp,true,aalang::OBSERVE);
        } |
        ostr ',' string {
            std::string* tmp=new std::string("o:" + *$2.str);
            delete $2.str;
            if (obj->check_name(tmp,$n2.start_loc.pathname,$n2.start_loc.line)) {
                raise_name_error($n2.start_loc,(Parser*)_parser,tmp);
            }
            obj->set_name(tmp,false,aalang::OBSERVE);
        } ;


tag_content: (comment|guard|adapter|tag|act)*;

tag: 'tag' tstr {
            abg_stack.push(guard);
            abg_stack.push(body);
            abg_stack.push(adapter);
            guard=false;body=true;adapter=false; } '{' tag_content '}' {
            if (!guard) {
                obj->empty_guard();
            }
            if (!adapter) {
                obj->empty_adapter();
            }
            obj->next_tag();
            adapter=abg_stack.top();abg_stack.pop();
            body=abg_stack.top();abg_stack.pop();
            guard=abg_stack.top();abg_stack.pop();
        };

tstr:   string          {
            if (obj->check_name($0.str,$n0.start_loc.pathname,$n0.start_loc.line)) {
                raise_name_error($n0.start_loc,(Parser*)_parser,$0.str);
            }
            obj->set_tagname($0.str,true);
        } |
        tstr ',' string {
            if (obj->check_name($2.str,$n2.start_loc.pathname,$n2.start_loc.line)) {
                raise_name_error($n2.start_loc,(Parser*)_parser,$2.str);
            }
            obj->set_tagname($2.str);
        } ;

push: 'push' '{' bstr '}' {
            obj->set_push($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col);
        } ;

pop:  'pop' '{' bstr '}' {
            obj->set_pop ($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

language: language_kw cpp    { if (!obj) obj=new aalang_cpp  ; obj->set_parser((Parser*)_parser); } starter ';'? |
          language_kw java   { if (!obj) obj=new aalang_java ; obj->set_parser((Parser*)_parser); } starter ';'? |
          language_kw python { if (!obj) obj=new aalang_py   ; obj->set_parser((Parser*)_parser); } starter ';'? ;

language_kw:  'language' | 'language:';

cpp: '"' cpp_kw '"' | cpp_kw ;

cpp_kw: 'C++' | 'cpp' | 'c++' ;

java: '"' java_kw '"' | java_kw ;

java_kw: 'oak' | 'green' | 'java' ;

python: '"' python_kw '"' | python_kw ;

python_kw: 'Python' | 'python' | 'py';

starter: |
        '{' bstr '}' {
            obj->set_starter($1.str,$n1.start_loc.pathname,$n1.start_loc.line,$n1.start_loc.col); };

variables: 'variables' '{' bstr '}' {
            obj->set_variables($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); };

istate: 'initial_state' '{' bstr '}' {
            obj->set_istate($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

ainit: 'adapter_init' '{' bstr '}' {
            obj->set_ainit($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

aexit: 'adapter_exit' '{' bstr '}' {
            obj->set_aexit($2.str,$n2.start_loc.pathname,$n2.start_loc.line,$n2.start_loc.col); } ;

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
