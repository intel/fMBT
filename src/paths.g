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
#include <vector>
#include <sstream>

typedef struct _node {
  std::string* str;
  std::vector<std::string*>* strvec;
} node;

int paths_node_size = sizeof(node);

#define D_ParseNode_User node
std::vector<std::string*> *paths_ff,*paths_tt,*paths_dd;
}

paths: 'from' strvec 'to' strvec opt_drop {
            *paths_ff=*$1.strvec;
            *paths_tt=*$3.strvec;
            *paths_dd=*$4.strvec;
            delete $1.strvec;
            delete $3.strvec;
            delete $4.strvec;
        };

opt_drop: { $$.strvec = new std::vector<std::string*>; }
    | 'drop' strvec { $$.strvec = $1.strvec; } ;

strvec: string { $$.strvec = new std::vector<std::string*>;
                 $$.strvec->push_back($0.str);
               }
    | strvec string {
            $$.strvec=$0.strvec;
            $$.strvec->push_back($1.str);
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } |
        "\'([^\'\\]|\\[^])*\'" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;
