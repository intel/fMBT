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

/*
 * Parser for xrules files. If compiled with CAPI, parser implements a
 * C API, otherwise expected to be called with a Lts_xrules instance.
 */

#include <stdlib.h>
#include <string>
typedef struct _node {
  unsigned int val;
  std::string* str;
} node;
#define D_ParseNode_User node

int xrules_node_size=sizeof(node);

#ifdef CAPI

#include "dparse.h"
#include "helper.hh"
#include <string.h>

extern D_ParserTables parser_tables_xrules;

void (*add_file_cb)(unsigned int, const char*) = 0;
void (*add_result_action_cb)(const char*) = 0;
void (*add_component_cb)(unsigned int, const char*) = 0;

extern "C" {
    int xrules_file(void (*f)(unsigned int, const char*)) {
        add_file_cb = f; return f != NULL; }
    int xrules_result_action(void (*f)(const char*)) {
        add_result_action_cb = f; return f != NULL;}
    int xrules_component(void (*f)(unsigned int, const char*)) {
        add_component_cb = f; return f != NULL;}
    int xrules_load(const char* filename) {
        D_Parser* p = new_D_Parser(&parser_tables_xrules, xrules_node_size);
        p->loc.pathname = filename;
        char* s = readfile(filename);
        dparse(p, s, strlen(s));
        int ret=p->syntax_errors;
        free(s);
        free_D_Parser(p);
        return ret;
    }
}

namespace xrules_local {
    void add_file(unsigned int index, std::string& filename)
    {
        if (add_file_cb) add_file_cb(index, filename.c_str());
    }
    void add_result_action(std::string* name)
    {
        if (add_result_action_cb) add_result_action_cb(name->c_str());
    }
    void add_component(unsigned int index, std::string& name)
    {
        if (add_component_cb) add_component_cb(index, name.c_str());
    }
}
#define PREFIX xrules_local::

#else /* (ifdef CAPI) parser for Lts_xrules class */

#include "lts_xrules.hh"
Lts_xrules* xobj;
#define PREFIX xobj->

#endif
}

xrules_file: filename+ rule+;

filename: int '=' string { PREFIX add_file($0.val,*$2.str); delete $2.str; $2.str=NULL; };

rule: | component+ '->' string { PREFIX add_result_action($2.str); delete $2.str; };

component: '(' int ',' string ')' { PREFIX add_component($1.val,*$3.str); delete $3.str; $3.str=NULL; };

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

int: istr { $$.val = atoi($n0.start_loc.s); };

istr: "[0-9]+";
