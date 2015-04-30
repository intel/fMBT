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

#ifndef __date_node__h__
#define __date_node__h__

typedef struct _date_node {
  GDateTime* date;
  bool rel;
  long i;
  int year,month,day,hour,min,sec;
  GTimeZone *zone;
  _date_node():date(NULL),rel(false),i(0),
          year(0),month(0),day(0),hour(0),min(0),sec(0),zone(NULL)
  { }

  _date_node(int _y,int _m,int _d,int _h,int _mi, int s):date(NULL),rel(true),i(0),
      year(_y),month(_m),day(_d),hour(_h),min(_mi),sec(s),zone(NULL)
      { }
} date_node;

#endif
