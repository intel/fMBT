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
std::vector<std::string> anames;
int action=1;
}

lang: model* ;

model: 'model' { anames.clear(); } namestr '{' language variables istate action* '}' {
            printf("public:\n");
            printf("int adapter_execute(int action) {\n");
            printf("\tswitch(action) {\n");

            for(unsigned i=1;i<action;i++) {
                printf("\t\tcase %i:\n",i);
                printf("\t\treturn action%i_adapter();\n\t\tbreak;\n",i);
            }
            printf("\t\tdefault:\n");
            printf("\t\treturn 0;\n");
            printf("\t};\n") ;
            printf("}\n") ;

            printf("int model_execute(int action) {\n");            

            printf("\tswitch(action) {\n");

            for(unsigned i=1;i<action;i++) {
                printf("\t\tcase %i:\n",i);
                printf("\t\taction%i_body();\n\t\treturn %i;\n\t\tbreak;\n",i,i);
            }
            printf("\t\tdefault:\n");
            printf("\t\treturn 0;\n");
            printf("\t};\n") ;
            printf("}\n") ;

            printf("int getActions(int** act) {\n");
            printf("\tactions.clear();\n");
            for(unsigned i=1;i<action;i++) {
                printf("\tif (action%i_guard()) {\n",i);
                printf("\t\tactions.push_back(%i);\n",i);
                printf("\t}\n");
            }
            printf("\t*act=&actions[0];\n");
            printf("\treturn actions.size();\n");
            printf("}\n");

            printf("};\n");
        };
language: 'language:' 'C++' ';';

namestr: { printf("class _gen_"); } unquoted_string { printf("%s: public aal {\nprivate:\n\t", $1.str->c_str()); };

name: 'name' ':' string ';' { anames.push_back(*$2.str); printf("%s",$2.str->c_str()); delete $2.str; $2.str=NULL; } ;

variables: 'variables' '{' bstr '}' { printf("//variables\n%s\n",$2.str->c_str()); } ;

istate: 'initial_state' '{' bstr '}' ;

action: 'action' '{' { printf("\n\t//action%i: ",action); } name { printf("\n"); } guard body adapter '}' { action++; } ;

guard: 'guard' '()' '{' bstr '}' { printf("bool action%i_guard() {\n%s}\n",action,$3.str->c_str()); } ;

body: 'body' '()' '{' bstr '}' { printf("void action%i_body() {\n%s}\n",action,$3.str->c_str()); } ;

adapter: 'adapter' '()' '{' bstr '}' { printf("int action%i_adapter() {\n%s}\n",action,$3.str->c_str()); }|;

bstr: "([^{}])*" { $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s); } |
        '{'bstr'}' { $$.str = new std::string(std::string("{")+*$1.str+std::string("}")); delete $1.str;
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

unquoted_string: "([a-zA-Z]*)" { $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s); };
