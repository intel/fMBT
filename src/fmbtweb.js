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


function send_to_server(response, callback) {
    url = "/fMBTweb." + response;

    var xmlHttp = window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject("MSXML2.XMLHTTP.3.0");

    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4) callback(xmlHttp);
    }
    xmlHttp.open("GET", url, true);
    xmlHttp.send();
}

function eval_response(xmlHttp) {
    try {
	eval_result = eval(xmlHttp.responseText);
    } catch (err) {
	eval_result = "fMBTweb error: " + err.description;
    }
    send_to_server(JSON.stringify(eval_result), eval_response);
}

send_to_server(null, eval_response);
