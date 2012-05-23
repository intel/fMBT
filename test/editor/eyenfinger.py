# fMBT, free Model Based Testing tool
# Copyright (c) 2012, Intel Corporation.
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

"""
eyenfinger - GUI testing library based on OCR and X event generation
"""

import time
import subprocess
import re
import math
import htmlentitydefs

g_hocr = ""

g_words = {}

g_lastWindow = None

# windowsOffsets maps window-id to (x, y) pair.
g_windowOffsets = {}
# windowsSizes maps window-id to (width, height) pair.
g_windowSizes = {}

SCREENSHOT_FILENAME = "/tmp/eyesnfinger.png"

MOUSEEVENT_MOVE, MOUSEEVENT_CLICK, MOUSEEVENT_DOWN, MOUSEEVENT_UP = range(4)

class BadMatch (Exception):
    pass

class BadWindowName (Exception):
    pass

def _log(msg):
    file("/tmp/eyenfinger.log", "a").write("%13.2f %s\n" % 
                                            (time.time(), msg))

def runcmd(cmd):
    _log("runcmd: " + cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.stdout.read()
    _log("stdout: " + output)
    _log("stderr: " + p.stderr.read())
    return p.wait(), output

def iRead(windowId = None):
    global g_hocr
    global g_lastWindow
    global g_words

    iUseWindow(windowId)

    # take a screenshot
    runcmd("xwd -root -screen -out %s.xwd && convert %s.xwd -crop %sx%s+%s+%s '%s'" %
           (SCREENSHOT_FILENAME, SCREENSHOT_FILENAME,
            g_windowSizes[g_lastWindow][0], g_windowSizes[g_lastWindow][1],
            g_windowOffsets[g_lastWindow][0], g_windowOffsets[g_lastWindow][1],
            SCREENSHOT_FILENAME))
    
    # convert to text
    _, g_hocr = runcmd("convert %s -sharpen 5 -filter Mitchell -resize 1920x1600 -level 40%%,70%%,5.0 -sharpen 5 %s && tesseract %s %s hocr && cat %s.html" % (
            SCREENSHOT_FILENAME, SCREENSHOT_FILENAME+"-big.png",
            SCREENSHOT_FILENAME+"-big.png", SCREENSHOT_FILENAME,
            SCREENSHOT_FILENAME))

    # store every word and its coordinates
    g_words = _hocr2words(g_hocr)
    for w in sorted(g_words.keys()):
        _log("%20s %s %s" % (w, g_words[w][0][0], g_words[w][0][1]))

    # convert word coordinates to the unscaled pixmap
    orig_width, orig_height = g_windowSizes[g_lastWindow][0], g_windowSizes[g_lastWindow][1]

    scaled_width, scaled_height = re.findall('bbox 0 0 ([0-9]+)\s*([0-9]+)', runcmd("grep ocr_page %s.html | head -n 1" % (SCREENSHOT_FILENAME,))[1])[0]
    scaled_width, scaled_height = float(scaled_width), float(scaled_height)

    for word in g_words:
        for appearance, (wordid, middle, bbox) in enumerate(g_words[word]):
            g_words[word][appearance] = \
                (wordid,
                 (int(middle[0]/scaled_width * orig_width),
                  int(middle[1]/scaled_height * orig_height)),
                 (int(bbox[0]/scaled_width * orig_width),
                  int(bbox[1]/scaled_height * orig_height),
                  int(bbox[2]/scaled_width * orig_width),
                  int(bbox[3]/scaled_height * orig_height)))
            _log(word + ': (' + str(bbox[0]) + ', ' + str(bbox[1]) + ')')

def iClickWord(word, appearance=1, pos=(0,0), match=0.33, mousebutton=1, mouseevent=1):
    """
    Parameters:
        word       - word that should be clicked
        appearance - if word appears many times, appearance to
                     be clicked. Defaults to the first one.
        pos        - position of the word that should be clicked.
                     (0,0) - middle, (-1,0) - left, (1,0) - right,
                     (0,-1) - top, (0,1) - bottom, (-1,-1) - top-left...
                     Defaults to the middle.
    """
    windowId = g_lastWindow
    scored_words = []
    for w in g_words:
        scored_words.append((_score(w, word) * _score(word, w), w))
    scored_words.sort()
    
    assert len(scored_words) > 0, "No words found"

    best_score =  math.sqrt(scored_words[-1][0])

    if best_score < match:
        raise BadMatch('No matching word for "%s". The best candidate "%s" with score %.2f, required %.2f' %
                            (word, scored_words[-1][1], best_score, match))
    # Parameters should contain some hints on which appearance of the
    # word should be clicked. At the moment we'll use the first one.
    middle_x, middle_y = g_words[scored_words[-1][1]][appearance-1][1]
    _log('G_WORD ENTRY %s' % (g_words[scored_words[-1][1]][appearance-1],))
    left, top, right, bottom = g_words[scored_words[-1][1]][appearance-1][2]

    _log('left=%s, top=%s, right=%s, bottom=%s, midx=%s, midy=%s' % (left, top, right, bottom, middle_x, middle_y))
    click_x = middle_x + pos[0]*(right-middle_x) + g_windowOffsets[windowId][0]
    click_y = middle_y + pos[1]*(bottom-middle_y) + g_windowOffsets[windowId][1]
    
    _log('iClickWord("%s"): click "%s" (middle: %s, click: %s)' %
        (word, scored_words[-1][1], (middle_x, middle_y), (click_x, click_y)))

    if mouseevent == MOUSEEVENT_CLICK:
        params = "'mouseclick %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_DOWN:
        params = "'mousedown %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_UP:
        params = "'mouseup %s'" % (mousebutton,)
    else:
        params = ""

    # use xte from the xautomation package
    runcmd("xte 'mousemove %s %s' %s" % (click_x, click_y, params))
    return best_score

def iType(word):
    """
    Send keypress events.
    word can be
      - string containing letters and numbers
        each letter/number is sent with press and release events
      - list of keys and/or (key, event) pairs:
        - each key is sent with press and release events
        - for each (key, event), corresponding event is sent.
          event is 'press' or 'release'.
      - list of tuples (key1, key2, ..., keyn)
        this will generate 2n events:
        key1 press, key2 press, ..., keyn press
        keyn release, ..., key2 release, key1 release

    Keynames are defined in keysymdef.h.

    Example:
    iType('hello')
    iType([('Shift_L', 'press'), 'h', 'e', ('Shift_L', 'release'), 'l', 'l', 'o'])
    iType([('Control_L', 'Alt_L', 'Delete')])
    """
    args = []
    for char in word:
        if type(char) == tuple:
            if char[1].lower() == 'press':
                args.append("'keydown %s'" % (char[0],))
            elif char[1].lower() == 'release':
                args.append("'keyup %s'" % (char[0],))
            else:
                rest = []
                for key in char:
                    args.append("'keydown %s'" % (key,))
                    rest.insert(0, "'keyup %s'" % (key,))
                args = args + rest
        else:
            # char is keyname or single letter/number
            args.append("'key %s'" % (char,))
    runcmd("xte %s" % (' '.join(args),))

def _score(w1, w2):
    # This is just a 10 minute hack without deep thought.
    # Better scoring should be considered.
    positions = []
    for char in w1:
        positions.append([])
        pos = w2.find(char)
        while pos > -1:
            positions[-1].append(pos)
            pos = w2.find(char, pos + 1)
    score = 0.0
    maxscore_per_char = 1.0 / len(w1)
    next_positions = [0]
    for i in xrange(len(w1)):
        for p in positions[i]:
            if p in next_positions:
                score += maxscore_per_char
        next_positions = [pos+1 for pos in positions[i]]
    return score

def _hocr2words(hocr):
    rv = {}
    hocr = hocr.replace("<strong>","").replace("</strong>","")
    hocr.replace("&#39;", "'")
    for name, code in htmlentitydefs.name2codepoint.iteritems():
        if code < 128:
            hocr = hocr.replace('&' + name + ';', chr(code))
    ocr_word = re.compile('''<span class=['"]ocr_word["'] id=['"]([^']*)["'] title=['"]bbox ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)["'][^>]*>([^<]*)</span>''')
    for word_id, bbox_left, bbox_top, bbox_right, bbox_bottom, word in ocr_word.findall(hocr):
        bbox_left, bbox_top, bbox_right, bbox_bottom = \
            int(bbox_left), int(bbox_top), int(bbox_right), int(bbox_bottom)
        if not word in rv:
            rv[word] = []
        middle_x = (bbox_right + bbox_left) / 2.0
        middle_y = (bbox_top + bbox_bottom) / 2.0
        rv[word].append((word_id, (middle_x, middle_y), (bbox_left, bbox_top, bbox_right, bbox_bottom)))
    return rv

def iUseWindow(windowIdOrName = None):
    global g_lastWindow
    if windowIdOrName == None:
        if g_lastWindow == None:
            g_lastWindow = iActiveWindow()
    elif windowIdOrName.startswith("0x"):
        g_lastWindow = windowIdOrName
    else:
        g_lastWindow = runcmd("xwininfo -name '%s' | awk '/Window id: 0x/{print $4}'" %
                              (windowIdOrName,))[1].strip()
        if not g_lastWindow.startswith("0x"):
            raise BadWindowName('Cannot find window id for "%s" (got: "%s")' %
                                (windowIdOrName, g_lastWindow))
    _, output = runcmd("xwininfo -id %s | awk '/Width:/{w=$NF}/Height:/{h=$NF}/Absolute upper-left X/{x=$NF}/Absolute upper-left Y/{y=$NF}END{print x\" \"y\" \"w\" \"h}'" %
                       (g_lastWindow,))
    offset_x, offset_y, width, height = output.split(" ")
    g_windowOffsets[g_lastWindow] = (int(offset_x), int(offset_y))
    g_windowSizes[g_lastWindow] = (int(width), int(height))
    return g_lastWindow

def iActiveWindow(windowId = None):
    """ return id of active window, in '0x1d0f14' format """
    if windowId == None:
        _, output = runcmd("xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}'")
        windowId = output.strip()

    return windowId
