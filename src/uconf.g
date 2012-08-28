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

void sdel(std::vector<std::string*>* strvec)
{
    for(unsigned i=0;i<strvec->size();i++) {
        delete (*strvec)[i];
    }
    delete strvec;
}

typedef struct _node {
  int val;
  std::string* str;
  std::vector<std::string*>* strvec;
} node;
#define D_ParseNode_User node
#include "of.hh"
OutputFormat* uconf_obj;
}

conf_file: model (usecase|testcase)+;

model: 'model' '=' string { uconf_obj->set_model(*$2.str); delete $2.str; } ;

usecase: string '=' string { uconf_obj->add_uc(*$0.str,*$2.str); delete $0.str; delete $2.str; } ;

testcase: 'report' string 'from' strvec 'to' strvec opt_drop { uconf_obj->add_report(*$1.str,
                *$3.strvec,
                *$5.strvec,
                *$6.strvec);
            delete $1.str;
            sdel($3.strvec);
            sdel($5.strvec);
            sdel($6.strvec);
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

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;
