{
/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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
#include <map>
#include <stdio.h>

typedef struct _node {
  int val;
  struct { int a,b,c; } setspec;
  std::string* str;
  std::pair<int,int> s;
  std::vector<std::string* >* strvec;
  std::vector<std::pair<std::string*,std::pair<int,int> > >* filtervec;
} node;

std::vector<std::string*> *set_ff,*set_tt,*set_dd;
std::vector<std::pair<std::string*,std::pair<int,int> > >* filtervec;
#define D_ParseNode_User node
}

testcase: setspec 'from' strvec 'to' strvec opt_drop '->' filtervec {
            *set_ff=*$2.strvec;
            *set_tt=*$4.strvec;
            *set_dd=*$5.strvec;
            *filtervec = *$7.filtervec;
            delete $2.strvec;
            delete $4.strvec;
            delete $5.strvec;
            delete $7.filtervec;
        };

setspec: oint ':' oint ':' oint {
            if ($0.val==-1) {
                $$.setspec.a=0;
            } else {
                $$.setspec.a=$0.val;
            }

            $$.setspec.b=$2.val;

            if ($4.val==-1) {
                $$.setspec.c=1;
            } else {
                $$.setspec.c=$4.val;
            }
        } | {
            $$.setspec.a=0;
            $$.setspec.b=1;
            $$.setspec.c=1;
        } ;

filtervec: filtervec string ipair { 
            $$.filtervec=$0.filtervec;
            $$.filtervec->push_back(std::pair<std::string*, std::pair<int,int> >($1.str,$2.s));
        } | string ipair {
            $$.filtervec = new std::vector<std::pair<std::string*, std::pair<int,int> > >;
            $$.filtervec->push_back(std::pair<std::string*, std::pair<int,int> >($0.str,$1.s));

        } ;

opt_drop: { $$.strvec = new std::vector<std::string*>; }
    | 'drop' strvec { $$.strvec = $1.strvec; } ;

oint: { $$.val=-1; } |
        int { $$.val=$0.val; } ;

ipair: ':' oint ':' oint {
            int l=$1.val;
            int r=$3.val;
            // I hate ($1.val==-1)?.. syntax
            if (l==-1) {
                l=0;
            }
            if (r==-1) {
                r=1;
            }
            $$.s=std::pair<int,int>(l,r);
        } | { $$.s=std::pair<int,int>(0,1); } ;

strvec: string { $$.strvec = new std::vector<std::string*>;
                 $$.strvec->push_back($0.str);
               }
    | strvec string {
            $$.strvec=$0.strvec;
            $$.strvec->push_back($1.str);
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;

int: istr { $$.val = atoi($n0.start_loc.s); };

istr: "[0-9]+";
