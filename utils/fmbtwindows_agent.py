# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

import ctypes
import os
import struct
import time
import zlib

def version():
    return "0.0a"

# Struct to retrieve positions of a monitor
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]
    def dump(self):
        return {'left': int(self.left), 'right': int(self.right),
                'top': int(self.top), 'bottom': int(self.bottom)}

def get_pixels(monitor):
    ''' Retrieve pixels from a monitor '''
    ret = ""
    hmon = monitor['hdc']
    width = monitor['width']
    height = monitor['height']
    left = monitor['left']
    top = monitor['top']
    user = ctypes.windll.user32
    gdi = ctypes.windll.gdi32
    metrics = ctypes.windll.user32.GetSystemMetrics(0)
    SRCCOPY = 0xCC0020
    DIB_RGB_COLORS = 0
    srcdc = ctypes.windll.user32.GetWindowDC(0)
    memdc = ctypes.windll.gdi32.CreateCompatibleDC(srcdc)
    bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(srcdc, width, height)
    ctypes.windll.gdi32.SelectObject(memdc, bmp)
    ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, srcdc, left, top, SRCCOPY)
    bmp_header = struct.pack('LHHHH', struct.calcsize('LHHHH'), width, height, 1, 24)
    c_bmp_header = ctypes.c_buffer(bmp_header)
    c_bits =       ctypes.c_buffer(' ' * (height * ((width * 3 + 3) & -4)))
    got_bits =     ctypes.windll.gdi32.GetDIBits(memdc, bmp, 0, height,
                                                 c_bits, c_bmp_header, DIB_RGB_COLORS)
    ret="P6\n%d %d\n255\n" % ( monitor['width'] ,monitor['height'] )
    rv = [ret]
    for i in xrange(height-1,-1,-1):
        start_index =int( i * ((width * 3 + 3) & -4) )
        end_index   =int( start_index+ width*3 )
        rv.append(c_bits.__getslice__(start_index, end_index))
    return "".join(rv)

def enum_display_monitors():
    ''' Get positions and handles of one or more monitors. '''

    def _callback(monitor, dc, rect, data):
        infos = rect.contents.dump()
        infos['hmon'] = monitor
        infos['hdc'] = dc
        results.append(infos)
        return 0

    results = []
    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                         ctypes.POINTER(RECT), ctypes.c_double)
    callback = MonitorEnumProc(_callback)
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0)
    return results

_g_monitors = enum_display_monitors()

def screenshot(monitor_index):
    if not 0 <= monitor_index < len(_g_monitors):
        raise ValueError(("Invalid monitor index for screenshot(): %s "
                          "must be 0..%s") % (monitor_index, len(_g_monitors)-1))
    monitor = _g_monitors[monitor_index]
    monitor['width'] = monitor['right'] - monitor['left']
    monitor['height'] = monitor['bottom'] - monitor['top']
    return zlib.compress(get_pixels(monitor))

if __name__ == '__main__':
    start = time.time()
    screenshot(0)
    end = time.time()
    print "total screenshot time:", end-start
