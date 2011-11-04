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
#include <string>
#include <vector>

#ifndef DROI
#include <boost/regex.hpp>
#endif

extern bool human_readable;
int  find(const std::vector<std::string>&,const std::string);
bool isInputName(const std::string& name);
bool isOutputName(const std::string& name);
void clear_whitespace(std::string& s);
void clear_coding(std::string& s);
bool isxrules(std::string& s);
std::string filetype(std::string& s);
char* readfile(const char* filename);
std::string capsulate(std::string s);
char* escape_string(const char* msg);
std::string removehash(std::string& s);
void string2vector(char* s,std::vector<int>& a);
#ifndef DROI
std::string replace(boost::regex& expression,
		    const char* format_string,
 		    std::string::iterator first,
		    std::string::iterator last);
#endif
