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

Configuring
-----------

autoconfigure() evaluates number of preprocessing filters to give the
best result on finding given words from given image. Example:

python -c '
from eyenfinger import *
autoconfigure("screenshot.png", ["Try", "to", "find", "these", "words"])
'


evaluatePreprocessFilter() highlights words detected on given image. Example:

python -c '
from eyenfinger import *
evaluatePreprocessFilter("screenshot.png", "-sharpen 5 -resize 1600x", ["File", "View"])
'

setPreprocessFilter() sets given filter to be used when reading text from images.

Debugging
---------

iClickWord() capture parameter visualises coordinates to be clicked. Example:

python -c '
from eyenfinger import *
setPreprocessFilter("-sharpen 5 -filter Mitchell -resize 1600x -level 40%,50%,3.0")
iRead(source="screenshot.png")
iClickWord("[initial", clickPos=(-2,3), capture="highlight.png", dryRun=True)
'
"""

import time
import subprocess
import re
import math
import htmlentitydefs
import sys
import os

g_preprocess = "-sharpen 5 -filter Mitchell -resize 1920x1600 -level 40%%,70%%,5.0 -sharpen 5"

g_readImage = None

g_origImage = None

g_hocr = ""

g_words = {}

g_lastWindow = None

# windowsOffsets maps window-id to (x, y) pair.
g_windowOffsets = {None: (0,0)}
# windowsSizes maps window-id to (width, height) pair.
g_windowSizes = {}

SCREENSHOT_FILENAME = "/tmp/eyenfinger.png"

MOUSEEVENT_MOVE, MOUSEEVENT_CLICK, MOUSEEVENT_DOWN, MOUSEEVENT_UP = range(4)

# This is not complete list by any means.
# See keysymdef.h.
keys = [
    "BackSpace", "Tab", "Linefeed", "Clear", "Return", "Pause",
    "Scroll_Lock", "Sys_Req", "Escape", "Delete", "Home", "Left",
    "Up", "Right", "Down", "Prior", "Page_Up", "Next", "Page_Down",
    "End", "Begin", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
    "F9", "F10", "F11", "F12", "Shift_L", "Shift_R", "Control_L",
    "Control_R", "Caps_Lock", "Shift_Lock", "Meta_L", "Meta_R",
    "Alt_L", "Alt_R", "space", "exclam", "quotedbl", "numbersign",
    "dollar", "percent", "ampersand", "apostrophe", "quoteright",
    "parenleft", "parenright", "asterisk", "plus", "comma", "minus",
    "period", "slash", "0", "1", "2", "3", "4", "5", "6", "7", "8",
    "9", "colon", "semicolon", "less", "equal", "greater", "question",
    "at", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
    "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y",
    "Z", "bracketleft", "backslash", "bracketright", "asciicircum",
    "underscore", "grave", "quoteleft", "a", "b", "c", "d", "e", "f",
    "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
    "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar",
    "braceright"]

class BadMatch (Exception):
    pass

class BadWindowName (Exception):
    pass

try:
    import fmbt
    def _log(msg):
        fmbt.adapterlog("eyenfinger: %s" % (msg,))

except ImportError:
    def _log(msg):
        file("/tmp/eyenfinger.log", "a").write("%13.2f %s\n" %
                                               (time.time(), msg))


try:
    import ctypes
    _libpath = ["",
                "." + os.path.sep,
                "." + os.path.sep + ".libs" + os.path.sep,
                os.path.dirname(__file__) + os.path.sep,
                os.path.dirname(__file__) + os.path.sep + ".libs" + os.path.sep]
    for _dirname in _libpath:
        try:
            eye4graphics = ctypes.CDLL(_dirname + "eye4graphics.so")
            break
        except: pass
    else:
        raise ImportError("%s cannot load eye4graphics.so" % (__file__,))

    class Bbox(ctypes.Structure):
        _fields_ = [("left", ctypes.c_int32),
                    ("top", ctypes.c_int32),
                    ("right", ctypes.c_int32),
                    ("bottom", ctypes.c_int32),
                    ("error", ctypes.c_int32)]
except Exception, e:
    Bbox = None
    eye4graphics = None
    _log('Loading icon recognition library failed: "%s".' % (e,))


def runcmd(cmd):
    _log("runcmd: " + cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.stdout.read()
    _log("stdout: " + output)
    _log("stderr: " + p.stderr.read())
    return p.wait(), output

def setPreprocessFilter(preprocess):
    global g_preprocess
    g_preprocess = preprocess

def iRead(windowId = None, source = None, preprocess = "", ocr=True):
    global g_hocr
    global g_lastWindow
    global g_words
    global g_readImage
    global g_origImage

    if not source:
        iUseWindow(windowId)

        # take a screenshot
        runcmd("xwd -root -screen -out %s.xwd && convert %s.xwd -crop %sx%s+%s+%s '%s'" %
               (SCREENSHOT_FILENAME, SCREENSHOT_FILENAME,
                g_windowSizes[g_lastWindow][0], g_windowSizes[g_lastWindow][1],
                g_windowOffsets[g_lastWindow][0], g_windowOffsets[g_lastWindow][1],
                SCREENSHOT_FILENAME))
        source = SCREENSHOT_FILENAME
    else:
        iUseImageAsWindow(source)
    g_origImage = source

    if not ocr:
        return []

    # convert to text
    g_readImage = g_origImage + "-pp.png"
    _, g_hocr = runcmd("convert %s %s %s && tesseract %s %s -l eng hocr" % (
            g_origImage, g_preprocess, g_readImage,
            g_readImage, SCREENSHOT_FILENAME))

    # store every word and its coordinates
    g_words = _hocr2words(file(SCREENSHOT_FILENAME + ".html").read())

    # convert word coordinates to the unscaled pixmap
    orig_width, orig_height = g_windowSizes[g_lastWindow][0], g_windowSizes[g_lastWindow][1]

    scaled_width, scaled_height = re.findall('bbox 0 0 ([0-9]+)\s*([0-9]+)', runcmd("grep ocr_page %s.html | head -n 1" % (SCREENSHOT_FILENAME,))[1])[0]
    scaled_width, scaled_height = float(scaled_width), float(scaled_height)

    for word in sorted(g_words.keys()):
        for appearance, (wordid, middle, bbox) in enumerate(g_words[word]):
            g_words[word][appearance] = \
                (wordid,
                 (int(middle[0]/scaled_width * orig_width),
                  int(middle[1]/scaled_height * orig_height)),
                 (int(bbox[0]/scaled_width * orig_width),
                  int(bbox[1]/scaled_height * orig_height),
                  int(bbox[2]/scaled_width * orig_width),
                  int(bbox[3]/scaled_height * orig_height)))
            _log('found "' + word + '": (' + str(bbox[0]) + ', ' + str(bbox[1]) + ')')
    return sorted(g_words.keys())

def iVerifyWord(word, match=0.33, capture=None):
    """
    Verify that word can be found from previously iRead() image.

    Parameters:
        word       - word that should be checked
        match      - minimum matching score
        capture    - name of file where image of highlighted word and
                     clicked point are saved.

    Returns pair: score, matching_word

    Throws BadMatch error if could not find a matching word.
    """
    score, matching_word = findWord(word)

    if capture:
        drawWords(g_origImage, capture, [word], g_words)

    if score < match:
        raise BadMatch('No matching word for "%s". The best candidate "%s" with score %.2f, required %.2f' %
                            (word, matching_word, score, match))
    return score, matching_word

def iClickIcon(iconFilename, clickPos=(0.5,0.5), match=1.0, mousebutton=1, mouseevent=1, dryRun=False, capture=None):
    if not eye4graphics:
        _log('ERROR: iClickIcon("%s") called, but eye4graphics not loaded.' % (iconFilename))
        return False
    struct_bbox = Bbox(0,0,0,0,0)
    if match > 1.0:
        _log('iClickIcon("%s"): invalid match value, must be below 1.0. ' % (iconFilename,))
        return False
    threshold = int((1.0-match)*20)
    err = eye4graphics.findSingleIcon(ctypes.byref(struct_bbox), g_origImage, iconFilename, threshold)
    if err != 0:
        _log("findSingleIcon returned %s" % (err,))
        return False
    # TODO: pay attention to match and struct_bbox.error

    left, top, right, bottom = int(struct_bbox.left), int(struct_bbox.top), int(struct_bbox.right), int(struct_bbox.bottom)

    click_x = int(left + clickPos[0]*(right-left) + g_windowOffsets[g_lastWindow][0])
    click_y = int(top + clickPos[1]*(bottom-top) + g_windowOffsets[g_lastWindow][1])

    if mouseevent == MOUSEEVENT_CLICK:
        params = "'mouseclick %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_DOWN:
        params = "'mousedown %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_UP:
        params = "'mouseup %s'" % (mousebutton,)
    else:
        params = ""

    if capture:
        # TODO, highlight clicked position and detected icon
        # drawBbox(bbox)...
        pass

    if not dryRun:
        # use xte from the xautomation package
        runcmd("xte 'mousemove %s %s' %s" % (click_x, click_y, params))

    return struct_bbox.error

def iClickWord(word, appearance=1, clickPos=(0.5,0.5), match=0.33, mousebutton=1, mouseevent=1, dryRun=False, capture=None):
    """
    Click coordinates relative to the given word in previously iRead() image.

    Parameters:
        word       - word that should be clicked
        appearance - if word appears many times, appearance to
                     be clicked. Defaults to the first one.
        clickPos -   position to be clicked,
                     relative to word top-left corner of the bounding
                     box around the word. X and Y units are relative
                     to width and height of the box.  (0,0) is the
                     top-left corner, (1,1) is bottom-right corner,
                     (0.5, 0.5) is the middle point (default).
                     Values below 0 or greater than 1 click outside
                     the bounding box.
        capture -    name of file where image of highlighted word and
                     clicked point are saved.

    Returns pair: score, matching_word

    Throws BadMatch error if could not find a matching word.
    """
    windowId = g_lastWindow

    score, matching_word =  findWord(word)

    if score < match:
        raise BadMatch('No matching word for "%s". The best candidate "%s" with score %.2f, required %.2f' %
                            (word, matching_word, score, match))

    # Parameters should contain some hints on which appearance of the
    # word should be clicked. At the moment we'll use the first one.
    left, top, right, bottom = g_words[matching_word][appearance-1][2]

    click_x = int(left + clickPos[0]*(right-left) + g_windowOffsets[windowId][0])
    click_y = int(top + clickPos[1]*(bottom-top) + g_windowOffsets[windowId][1])

    _log('iClickWord("%s"): word "%s", match %.2f, bbox %s, window offset %s, click %s' %
        (word, matching_word, score,
         (left, top, right, bottom), g_windowOffsets[windowId],
         (click_x, click_y)))

    if mouseevent == MOUSEEVENT_CLICK:
        params = "'mouseclick %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_DOWN:
        params = "'mousedown %s'" % (mousebutton,)
    elif mouseevent == MOUSEEVENT_UP:
        params = "'mouseup %s'" % (mousebutton,)
    else:
        params = ""

    if capture:
        drawWords(g_origImage, capture, [word], g_words)
        drawClickedPoint(capture, capture, (click_x, click_y))

    if not dryRun:
        # use xte from the xautomation package
        runcmd("xte 'mousemove %s %s' %s" % (click_x, click_y, params))
    return score

def iType(word, delay=0.0):
    """
    Send keypress events.

    Parameters:
        word is either
            - a string containing letters and numbers.
              Each letter/number is using press and release events.
            - a list that contains
              - keys: each key is sent using press and release events.
              - (key, event)-pairs: the event (either "press" or "release")
                is sent.
              - (key1, key2, ..., keyn)-tuples. 2n events is sent:
                key1 press, key2 press, ..., keyn press,
                keyn release, ..., key2 release, key1 release.

            Keys are defined in keysymdef.h.

        delay is given as seconds between sent events

    Examples:
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
    usdelay = " 'usleep %s' " % (int(delay*1000000),)
    runcmd("xte %s" % (usdelay.join(args),))

def findWord(word, detected_words = None, appearance=1):
    """
    Returns pair (score, corresponding-detected-word)
    """
    if not detected_words:
        detected_words = g_words

    scored_words = []
    for w in detected_words:
        scored_words.append((_score(w, word), w))
    scored_words.sort()

    assert len(scored_words) > 0, "No words found"

    return scored_words[-1]

def _score(w1, w2):
    closeMatch = {
        '1l': 0.1,
        '1I': 0.2,
        'Il': 0.2
        }
    def levenshteinDistance(w1, w2):
        m = [range(len(w1)+1)]
        for j in xrange(len(w2)+1):
            m.append([])
            m[-1].append(j+1)
        i, j = 0, 0
        for j in xrange(1, len(w2)+1):
            for i in xrange(1, len(w1)+1):
                if w1[i-1] == w2[j-1]:
                    m[j].append(m[j-1][i-1])
                else:
                    # This is not part of Levenshtein:
                    # if characters often look similar,
                    # don't add full edit distance (1.0),
                    # use the value in closeMatch instead.
                    chars = ''.join(sorted(w1[i-1] + w2[j-1]))
                    if chars in closeMatch:
                        m[j].append(m[j-1][i-1]+closeMatch[chars])
                    else:
                        # Standard Levenshtein continues...
                        m[j].append(min(
                                m[j-1][i] + 1,  # delete
                                m[j][i-1] + 1,  # insert
                                m[j-1][i-1] + 1 # substitute
                                ))
        return m[j][i]
    return 1 - (levenshteinDistance(w1, w2) / float(max(len(w1),len(w2))))

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
        rv[word].append((word_id, (middle_x, middle_y),
                         (bbox_left, bbox_top, bbox_right, bbox_bottom)))
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

def iUseImageAsWindow(imagefilename):
    global g_lastWindow
    g_lastWindow = imagefilename
    _, output = runcmd("file '%s'" % (imagefilename,))
    output = output.split()
    image_width = int(output[output.index('x')-1])
    image_height = int(output[output.index('x')+1][:-1])

    g_windowOffsets[g_lastWindow] = (0, 0)
    g_windowSizes[g_lastWindow] = (image_width, image_height)
    return g_lastWindow

def iActiveWindow(windowId = None):
    """ return id of active window, in '0x1d0f14' format """
    if windowId == None:
        _, output = runcmd("xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}'")
        windowId = output.strip()

    return windowId

def drawWords(inputfilename, outputfilename, words, detected_words):
    """
    Draw boxes around words detected in inputfilename that match to
    given words. Result is saved to outputfilename.
    """
    draw_commands = ""
    for w in words:
        score, dw = findWord(w, detected_words)
        left, top, right, bottom = detected_words[dw][0][2]
        if score < 0.33:
            color = "red"
        elif score < 0.5:
            color = "brown"
        else:
            color = "green"
        draw_commands += """ -stroke %s -fill blue -draw "fill-opacity 0.2 rectangle %s,%s %s,%s" """ % (
            color, left, top, right, bottom)
        draw_commands += """ -stroke none -fill %s -draw "text %s,%s '%s'" """ % (
            color, left, top, w)
        draw_commands += """ -stroke none -fill %s -draw "text %s,%s '%.2f'" """ % (
            color, left, bottom+10, score)
    runcmd("convert %s %s %s" % (inputfilename, draw_commands, outputfilename))

def drawClickedPoint(inputfilename, outputfilename, clickedXY):
    x, y = clickedXY
    draw_commands = """ -stroke red -fill blue -draw "fill-opacity 0.2 circle %s,%s %s,%s" """ % (
        x, y, x + 20, y)
    draw_commands += """ -stroke none -fill red -draw "point %s,%s" """ % (x, y)
    runcmd("convert %s %s %s" % (inputfilename, draw_commands, outputfilename))

def evaluatePreprocessFilter(imagefilename, ppfilter, words):
    """
    Visualise how given words are detected from given image file when
    using given preprocessing filter.
    """
    global g_preprocess
    evaluatePreprocessFilter.count += 1
    preprocessed_filename = '%s-pre%s.png' % (imagefilename, evaluatePreprocessFilter.count)
    runcmd("convert '%s' %s '%s' && tesseract %s eyenfinger.autoconfigure hocr" %
           (imagefilename, ppfilter, preprocessed_filename,
            preprocessed_filename))
    detected_words = _hocr2words(file("eyenfinger.autoconfigure.html").read())
    scored_words = []
    for w in words:
        score, word = findWord(w, detected_words)
        scored_words.append((score, word, w))
    scored_words.sort()

    avg_score = sum([s[0] for s in scored_words])/float(len(scored_words))
    evaluatePreprocessFilter.scores.append( (scored_words[0][0] + avg_score, scored_words[0][0], avg_score, ppfilter) )
    evaluatePreprocessFilter.scores.sort()
    # set the best preprocess filter so far as a default
    g_preprocess = evaluatePreprocessFilter.scores[-1][-1]
    drawWords(preprocessed_filename, preprocessed_filename, words, detected_words)
    sys.stdout.write("%.2f %s %s %s\n" % (sum([s[0] for s in scored_words])/float(len(scored_words)), scored_words[0], preprocessed_filename, ppfilter))
    sys.stdout.flush()
evaluatePreprocessFilter.count = 0
evaluatePreprocessFilter.scores = []

def autoconfigure(imagefilename, words):
    """
    Search for image preprocessing configuration that will maximise
    the score of finding given words in the image.
    Returns configuration as a string.
    """

    # check image width
    _, output = runcmd("file '%s'" % (imagefilename,))
    output = output.split()
    image_width = int(output[output.index('x')-1])

    resize_filters = ['Mitchell', 'Catrom', 'Hermite', 'Gaussian']
    levels = [(20, 30), (20, 40), (20, 50),
              (30, 30), (30, 40), (30, 50),
              (40, 40), (40, 50), (40, 60),
              (50, 50), (50, 60), (50, 70),
              (60, 60), (60, 70), (60, 80)]

    zoom = [2]

    for f in resize_filters:
        for blevel, wlevel in levels:
            for z in zoom:
                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -filter %s -resize %sx -sharpen 5 -level %s%%,%s%%,3.0 -sharpen 5" % (f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -filter %s -resize %sx -level %s%%,%s%%,3.0 -sharpen 5" % (
                        f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -filter %s -resize %sx -level %s%%,%s%%,3.0" % (
                        f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -level %s%%,%s%%,3.0 -filter %s -resize %sx -sharpen 5" % (
                        blevel, wlevel, f, z * image_width),
                    words)

                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -level %s%%,%s%%,1.0 -filter %s -resize %sx" % (
                        blevel, wlevel, f, z * image_width),
                    words)

                evaluatePreprocessFilter(
                    imagefilename,
                    "-sharpen 5 -level %s%%,%s%%,10.0 -filter %s -resize %sx" % (
                        blevel, wlevel, f, z * image_width),
                    words)
