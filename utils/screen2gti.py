#!/usr/bin/env python

# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
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
#
# This is a small tool for converting UI events into fmbtgti interface
# method calls.

from PySide import QtCore
from PySide import QtGui

import getopt
import fmbtgti
import math
import os
import re
import sys
import time
import traceback

def error(msg, exitStatus=1):
    sys.stderr.write("screen2gti: %s\n" % (msg,))
    sys.exit(1)

def debug(msg, debugLevel=1):
    if opt_debug >= debugLevel:
        sys.stderr.write("screen2gti debug: %s\n" % (msg,))

def log(msg):
    sys.stdout.write("%s\n" % (msg,))
    sys.stdout.flush()

########################################################################
# Convert events to fmbtgti API calls

class GestureEvent(object):
    __slots__ = ["time", "event", "key", "pos"]
    def __init__(self, event, key, pos):
        self.time = time.time()
        self.event = event
        self.key = key
        self.pos = pos
    def __str__(self):
        return 'GestureEvent(time=%s, event="%s", key=%s, pos=%s)' % (
            self.time, self.event, self.key, self.pos)

def quantify(item, quantum):
    if not isinstance(item, tuple) and not isinstance(item, list):
        return int(item * (1/quantum)) * quantum
    else:
        return tuple([int(i * (1/quantum)) * quantum for i in item])

def gestureToGti(gestureEventList):
    timeQuantum = 0.1 # seconds
    locQuantum = 0.01 # 1.0 = full display height/width
    distQuantum = 0.1  # 1.0 = full dist from point to edge

    quantL = lambda v: quantify(v, locQuantum)
    quantT = lambda v: quantify(v, timeQuantum)

    el = gestureEventList

    firstEvent = el[0].event
    lastEvent = el[-1].event
    duration = el[-1].time - el[0].time
    distance = 0
    xDistance = 0
    yDistance = 0
    lastX, lastY = el[0].pos
    for e in el[1:]:
        xDistance += abs(lastX - e.pos[0])
        yDistance += abs(lastY - e.pos[1])
        distance += math.sqrt((lastX - e.pos[0])**2 +
                              (lastY - e.pos[1])**2)
        lastX, lastY = e.pos

    if firstEvent == "mousedown" and lastEvent == "mouseup":
        between_events = set([e.event for e in el[1:-1]])
        if between_events in (set(), set(["mousemove"])):
            # event sequence: mousedown, mousemove..., mouseup
            if duration < 3 * timeQuantum:
                # very quick event, make it single tap
                return ".tap((%s, %s))" % quantL(el[0].pos)
            elif distance < 3 * locQuantum:
                # neglible move, make it long tap
                return ".tap((%s, %s), hold=%s)" % (
                    quantL(el[0].pos) + quantT([duration]))
            elif xDistance < 3 * locQuantum:
                if el[-1].pos[1] < el[0].pos[1]:
                    direction = "north"
                    sdist = yDistance + (1-el[0].pos[1])
                else:
                    direction = "south"
                    sdist = yDistance + el[0].pos[1]
                # only y axis changed, we've got a swipe
                return '.swipe((%s, %s), "%s", distance=%s)' % (
                    quantL(el[0].pos) + (direction,) +
                    quantL([sdist]))
            elif yDistance < 3 * locQuantum:
                if el[-1].pos[0] < el[0].pos[0]:
                    direction = "west"
                    sdist = xDistance + (1-el[0].pos[0])
                else:
                    direction = "east"
                    sdist = xDistance + el[0].pos[0]
                # only y axis changed, we've got a swipe
                return '.swipe((%s, %s), "%s", distance=%s)' % (
                    quantL(el[0].pos) + (direction,) +
                    quantL([sdist]))
            else:
                return ".drag(%s, %s)" % (quantL(el[0].pos), quantL(el[-1].pos))
        else:
            return "unknown between events"
    else:
        return "unknown gesture"

########################################################################
# GUI

class MyScaleEvents(QtCore.QObject):
    """
    Catch scaling events: Ctrl++, Ctrl+-, Ctrl+wheel. Change
    attrowner's attribute "wheel_scale" accordingly. Finally call
    attrowner's wheel_scale_changed().
    """
    def __init__(self, mainwindow, attrowner, min_scale, max_scale):
        QtCore.QObject.__init__(self, mainwindow)
        self.min_scale  = min_scale
        self.max_scale  = max_scale
        self.attrowner  = attrowner
        self.mainwindow = mainwindow
        self.visibleTip = None
        self.selTop, self.selLeft = None, None
    def changeScale(self, coefficient):
        self.attrowner.wheel_scale *= coefficient
        if self.attrowner.wheel_scale < self.min_scale: self.attrowner.wheel_scale = self.min_scale
        elif self.attrowner.wheel_scale > self.max_scale: self.attrowner.wheel_scale = self.max_scale
        self.attrowner.wheel_scale_changed()
    def eventFilter(self, obj, event):
        if self.mainwindow._selectingBitmap:
            return self.eventToSelect(event)
        else:
            return self.eventToAPI(event)
    def eventToSelect(self, event):
        w = self.mainwindow
        print "selecting event..."
        if event.type() == QtCore.QEvent.MouseButtonPress:
            print "...start..."
            self.selLeft, self.selTop = self.posToAbs(event.pos)
            print "...at...", self.selTop, self.selLeft
        elif event.type() == QtCore.QEvent.MouseMove:
            print "...move..."
            if self.selTop != None:
                right, bottom = self.posToAbs(event.pos)
                print "...redraw...", self.selLeft, self.selTop, right, bottom
                w.drawRect(self.selLeft, self.selTop, right, bottom)
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            print "...stop..."
            if self.selTop != None:
                right, bottom = self.posToAbs(event.pos)
                w.selectBitmapDone(self.selLeft, self.selTop, right, bottom)
                self.selTop, self.selLeft = None, None
        return False
    def posToRel(self, pos):
        sbY = self.attrowner.verticalScrollBar().value()
        sbX = self.attrowner.horizontalScrollBar().value()
        wS = self.attrowner.wheel_scale
        x = (pos().x() + sbX) / wS / float(self.mainwindow.screenshotImage.width())
        y = (pos().y() + sbY) / wS / float(self.mainwindow.screenshotImage.height())
        return (x, y)
    def posToAbs(self, pos):
        sbY = self.attrowner.verticalScrollBar().value()
        sbX = self.attrowner.horizontalScrollBar().value()
        wS = self.attrowner.wheel_scale
        x = (pos().x() + sbX) / wS
        y = (pos().y() + sbY) / wS
        return (x, y)
    def eventToAPI(self, event):
        if event.type() == QtCore.QEvent.MouseMove:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mousemove", None, self.posToRel(event.pos)))
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if not self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = True
                self.mainwindow.gestureEvents = [
                    GestureEvent("mousedown", 0, self.posToRel(event.pos))]
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = False
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mouseup", 0, self.posToRel(event.pos)))
                s = gestureToGti(self.mainwindow.gestureEvents)
                cmd = opt_sut + s
                self.mainwindow.gestureEvents = []
                if self.mainwindow.screenshotButtonControl.isChecked():
                    debug("sending command %s" % (cmd,))
                    self.mainwindow.runStatement(cmd, autoUpdate=True)
                else:
                    debug("dropping command %s" % (cmd,))
                if self.mainwindow.editorButtonRec.isChecked():
                    self.mainwindow.editor.insertPlainText(cmd + "\n")
        elif event.type() == QtCore.QEvent.ToolTip:
            if not hasattr(self.attrowner, 'cursorForPosition'):
                return False
            filename = self.mainwindow.bitmapStringAt(event.pos())
            if filename == None:
                QtGui.QToolTip.hideText()
                self.visibleTip = None
            else:
                filepath = self.mainwindow.bitmapFilepath(filename)
                if filepath:
                    if self.visibleTip != filepath:
                        QtGui.QToolTip.hideText()
                        QtGui.QToolTip.showText(event.globalPos(), '%s<br><img src="%s">' % (filepath, filepath))
                else:
                    QtGui.QToolTip.showText(event.globalPos(), '%s<br>not in bitmapPath' % (filename,))
                self.visibleTip = filepath
            return True

        if event.type() == QtCore.QEvent.Wheel and event.modifiers() == QtCore.Qt.ControlModifier:
            coefficient = 1.0 + event.delta() / 1440.0
            self.changeScale(coefficient)
        return False

class fmbtdummy(object):
    class Device(object):
        def __init__(self, screenshotList=[]):
            self.scl = screenshotList
            self._paths = fmbtgti._Paths(
                os.getenv("FMBT_BITMAPPATH",""),
                os.getenv("FMBT_BITMAPPATH_RELROOT", ""))
        def refreshScreenshot(self):
            time.sleep(1)
            s = fmbtgti.Screenshot(screenshotFile=self.scl[0])
            s._paths = self._paths
            self._lastScreenshot = s
            self.scl.append(self.scl.pop(0)) # rotate screenshots
            return s
        def __getattr__(self, name):
            def argPrinter(*args, **kwargs):
                a = []
                for arg in args:
                    a.append(repr(arg))
                for k, v in kwargs.iteritems():
                    a.append('%s=%s' % (k, repr(v)))
                log("called: dummy.%s(%s)" % (name, ", ".join(a)))
                if name == "screenshot":
                    return self._lastScreenshot
                else:
                    return True
            return argPrinter

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self._bitmapSaveDir = os.getcwd()
        self._selectingBitmap = None

        self.mainwidget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout()
        self.mainwidget.setLayout(self.layout)

        self.splitter = QtGui.QSplitter(self.mainwidget)
        self.layout.addWidget(self.splitter,1)

        ### Screenshot widgets
        self.screenshotWidgets = QtGui.QWidget(self.mainwidget)
        self.screenshotWidgetsLayout = QtGui.QVBoxLayout()
        self.screenshotWidgets.setLayout(self.screenshotWidgetsLayout)

        self.screenshotButtons = QtGui.QWidget(self.screenshotWidgets)
        self.screenshotButtonsL = QtGui.QHBoxLayout()
        self.screenshotButtons.setLayout(self.screenshotButtonsL)
        self.screenshotButtonRefresh = QtGui.QPushButton(self.screenshotButtons,
                                                         text="Refresh",
                                                         checkable = True)
        self.screenshotButtonRefresh.clicked.connect(self.updateScreenshot)
        self.screenshotButtonsL.addWidget(self.screenshotButtonRefresh)
        self.screenshotButtonControl = QtGui.QPushButton(self.screenshotButtons,
                                                        text="Control",
                                                        checkable = True)
        self.screenshotButtonControl.clicked.connect(self.controlDevice)
        self.screenshotButtonsL.addWidget(self.screenshotButtonControl)
        self.screenshotButtonSelect = QtGui.QPushButton(self.screenshotButtons,
                                                         text="Select",
                                                         checkable = True)
        self.screenshotButtonSelect.clicked.connect(self.selectBitmap)
        self.screenshotButtonsL.addWidget(self.screenshotButtonSelect)
        self.screenshotWidgetsLayout.addWidget(self.screenshotButtons)

        def makeScalableImage(parent, qlabel):
            container = QtGui.QWidget(parent)
            layout = QtGui.QHBoxLayout()
            container.setLayout(layout)
            container.setStyleSheet("background-color:white;")

            qlabel.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
            qlabel.setScaledContents(True)
            qlabel.resize(QtCore.QSize(0,0))

            area = QtGui.QScrollArea(container)
            area.setWidget(qlabel)
            qlabel._scaleevents = MyScaleEvents(self, area, 0.1, 1.0)
            area.wheel_scale = 1.0
            area.wheel_scale_changed = lambda: qlabel.resize(area.wheel_scale * qlabel.pixmap().size())
            area.installEventFilter(qlabel._scaleevents)
            layout.addWidget(area)
            container.area = area
            container._layout = layout # protect from garbage collector
            return container

        self.screenshotQLabel = QtGui.QLabel(self.screenshotWidgets)
        self.screenshotQLabel.setMargin(0)
        self.screenshotQLabel.setIndent(0)
        self.screenshotContainer = makeScalableImage(self.screenshotWidgets, self.screenshotQLabel)
        self.screenshotWidgetsLayout.addWidget(self.screenshotContainer)
        self.screenshotImage = QtGui.QImage()

        self.screenshotQLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                self.screenshotImage))

        self.splitter.addWidget(self.screenshotWidgets)

        ### Editor widgets
        self.editorWidgets = QtGui.QWidget(self.mainwidget)
        self.editorWidgetsLayout = QtGui.QVBoxLayout()
        self.editorWidgets.setLayout(self.editorWidgetsLayout)

        self.editorButtons = QtGui.QWidget(self.editorWidgets)
        self.editorButtonsLayout = QtGui.QHBoxLayout()
        self.editorButtons.setLayout(self.editorButtonsLayout)

        self.editorButtonRec = QtGui.QPushButton("Rec", checkable=True)
        self.editorButtonRunSingle = QtGui.QPushButton("Run line")
        self.editorButtonRunSingle.clicked.connect(self.runSingleLine)
        self.editorButtonRunAll = QtGui.QPushButton("Run all")
        self.editorButtonsLayout.addWidget(self.editorButtonRec)
        self.editorButtonsLayout.addWidget(self.editorButtonRunSingle)
        self.editorButtonsLayout.addWidget(self.editorButtonRunAll)
        self.editorWidgetsLayout.addWidget(self.editorButtons)

        def makeScalableEditor(parent, font, EditorClass = QtGui.QTextEdit):
            editor = EditorClass()
            editor.setUndoRedoEnabled(True)
            editor.setLineWrapMode(editor.NoWrap)
            editor.setFont(font)
            editor._scaleevents = MyScaleEvents(self, editor, 0.1, 2.0)
            editor.wheel_scale = 1.0
            editor.wheel_scale_changed = lambda: (font.setPointSize(editor.wheel_scale * 12.0), editor.setFont(font))
            editor.installEventFilter(editor._scaleevents)
            return editor

        self.editorFont = QtGui.QFont()
        self.editorFont.setFamily('Courier')
        self.editorFont.setFixedPitch(True)
        self.editor = makeScalableEditor(self.mainwidget, self.editorFont)
        self.editorWidgetsLayout.addWidget(self.editor)
        self.splitter.addWidget(self.editorWidgets)

        self.setCentralWidget(self.mainwidget)

        ### Menus
        fileMenu = QtGui.QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)
        fileMenu.addAction("&Save", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QtGui.qApp.quit, "Ctrl+Q")

        viewMenu = QtGui.QMenu("&View", self)
        self.menuBar().addMenu(viewMenu)
        viewMenu.addAction("Refresh screenshot", self.updateScreenshot, "Ctrl+R")
        viewMenu.addAction("Zoom in editor", self.zoomInEditor, "Ctrl++")
        viewMenu.addAction("Zoom out editor", self.zoomOutEditor, "Ctrl+-")
        viewMenu.addAction("Zoom in screenshot", self.zoomInScreenshot, "Ctrl+.")
        viewMenu.addAction("Zoom out screenshot", self.zoomOutScreenshot, "Ctrl+,")

        bitmapMenu = QtGui.QMenu("&Bitmap", self)
        self.menuBar().addMenu(bitmapMenu)
        bitmapMenu.addAction("Select", self.selectBitmap, "Ctrl+B, Ctrl+S")
        bitmapMenu.addAction("Verify", self.verifyBitmap, "Ctrl+B, Ctrl+V")

        self.gestureEvents = []
        self.gestureStarted = False

    def bitmapStringAt(self, pos=None):
        filename = None
        if pos != None:
            cursor = self.editor.cursorForPosition(pos)
        else:
            cursor = self.editor.textCursor()
        pos = cursor.positionInBlock()
        lineno = cursor.blockNumber()
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        l = cursor.selectedText()
        start = l.rfind('"', 0, pos)
        end = l.find('"', pos)
        if -1 < start < end:
            quotedString = l[start+1:end]
            if quotedString.lower().rsplit(".")[-1] in ["png", "jpg"]:
                filename = quotedString
        return filename

    def bitmapFilepath(self, filename):
        try:
            filepath = sut.screenshot()._paths.abspath(filename)
            return filepath
        except ValueError:
            return None

    def invalidateScreenshot(self):
        self.screenshotButtonRefresh.setChecked(True)
        self.screenshotButtonRefresh.repaint()
        _app.processEvents()

    def runSingleLine(self, lineNumber=None):
        if lineNumber == None:
            line = self.editor.textCursor().block().text().strip()
            if self.runStatement(line):
                self.editor.moveCursor(QtGui.QTextCursor.Down, QtGui.QTextCursor.MoveAnchor)
        else:
            raise NotImplementedError

    def runStatement(self, statement, autoUpdate=False):
        if autoUpdate:
            self.invalidateScreenshot()
        log("running: %s" % (statement,))
        try:
            exec statement
            log("ok")
            rv = True
        except Exception, e:
            log("error:\n%s" % (traceback.format_exc(),))
            rv = False
        if autoUpdate:
            QtCore.QTimer.singleShot(1000, self.updateScreenshot)
        return rv

    def setFilename(self, filename):
        self._scriptFilename = filename

    def save(self):
        if self._scriptFilename:
            file(self._scriptFilename, "w").write(self.editor.toPlainText())

    def updateScreenshot(self):
        self.invalidateScreenshot()

        sut.refreshScreenshot().save("screen2gti.png")
        self.screenshotImage = QtGui.QImage()
        self.screenshotImage.load("screen2gti.png")
        self.updateScreenshotView()

    def updateScreenshotView(self):
        self.screenshotQLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                self.screenshotImage))
        self.screenshotContainer.area.setWidget(self.screenshotQLabel)
        self.screenshotContainer.area.wheel_scale_changed()
        self.screenshotButtonRefresh.setChecked(False)

    def verifyBitmap(self, filepath=None):
        if filepath == None:
            filename = self.bitmapStringAt()
            if filename:
                filepath = self.bitmapFilepath(filename)
                if filepath == None:
                    log('bitmap "%s" not in bitmapPath' % (filename,))
            else:
                log("no bitmap to verify")
        if filepath != None:
            log('TODO: verify: "%s"' % (filepath,))

    def controlDevice(self):
        if self.screenshotButtonControl.isChecked():
            if self._selectingBitmap:
                self.selectBitmapStop()
                self.screenshotButtonControl.setChecked(True)

    def selectBitmapStop(self):
        # already selecting, toggle
        if self._selectingBitmap != None:
            log('selecting bitmap "%s" canceled' % (self._selectingBitmap,))
            self._selectingBitmap = None
        self.screenshotButtonSelect.setChecked(False)
        self.screenshotButtonControl.setChecked(
            self._selectingToggledInteract)

    def selectBitmapDone(self, top, left, right, bottom):
        log('saving bitmap "%s"' % (self._selectingBitmap,))
        self.drawRect(top, left, right, bottom, True)
        time.sleep(1)
        self.drawRect(top, left, right, bottom, False)
        time.sleep(1)
        self.drawRect(top, left, right, bottom, True)
        self._selectingBitmap = None
        self.selectBitmapStop()

    def selectBitmap(self, filepath=None):
        if self._selectingBitmap:
            self.selectBitmapStop()
            return None

        if filepath == None:
            filename = self.bitmapStringAt()
            if filename:
                filepath = self.bitmapFilepath(filename)
                if filepath:
                    log('select replacement for "%s"' % (filepath,))
                else:
                    filepath = os.path.join(sut._paths.bitmapPath.split(":")[0],
                                            filename)
                    log('select new bitmap "%s"' % (filepath,))
                self._selectingBitmap = filepath
        elif filepath != None:
            log('select bitmap "%s"' % (filepath,))
            self._selectingBitmap = filepath

        if self._selectingBitmap:
            self.screenshotButtonSelect.setChecked(True)
            self._selectingToggledInteract = self.screenshotButtonControl.isChecked()
            self.screenshotButtonControl.setChecked(False)
        else:
            self.screenshotButtonSelect.setChecked(False)

    def drawRect(self, left, top, right, bottom, clear=False):
        if getattr(self, "_screenshotImageOrig", None) == None:
            self._screenshotImageOrig = self.screenshotImage.copy()
        else:
            self.screenshotImage = self._screenshotImageOrig.copy()
        if not clear:
            x1, y1, x2, y2 = left, top, right, bottom
            #y1 = top * self.screenshotImage.height()
            #x1 = left * self.screenshotImage.width()
            #y2 = bottom * self.screenshotImage.height()
            #x2 = right * self.screenshotImage.width()
            painter = QtGui.QPainter(self.screenshotImage)
            bgPen = QtGui.QPen(QtGui.QColor(0, 0, 32), 1)
            fgPen = QtGui.QPen(QtGui.QColor(64, 255, 128), 1)
            painter.setPen(bgPen)
            painter.drawRect(x1-2, y1-2, (x2-x1)+4, (y2-y1)+4)
            painter.drawRect(x1-1, y1-1, (x2-x1)+2, (y2-y1)+2)
            painter.setPen(fgPen)
            painter.drawRect(x1, y1, (x2-x1), (y2-y1))
        self.updateScreenshotView()

    def zoomInEditor(self):
        self.editor._scaleevents.changeScale(1.1)

    def zoomOutEditor(self):
        self.editor._scaleevents.changeScale(0.9)

    def zoomInScreenshot(self):
        self.screenshotQLabel._scaleevents.changeScale(1.1)

    def zoomOutScreenshot(self):
        self.screenshotQLabel._scaleevents.changeScale(0.9)


if __name__ == "__main__":

    opt_connect = ""
    opt_gti = None
    opt_sut = None
    opt_debug = 0
    supported_platforms = ['android', 'tizen', 'x11', 'vnc', 'dummy']

    opts, remainder = getopt.getopt(
        sys.argv[1:], 'hd:p:',
        ['help', 'device=', 'platform=', 'debug'])

    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print __doc__
            sys.exit(0)
        elif opt in ['--debug']:
            opt_debug += 1
        elif opt in ['-d', '--device']:
            opt_connect = arg
        elif opt in ['-p', '--platform']:
            opt_gti = arg
            if arg in ['android', 'tizen', 'dummy']:
                opt_gticlass = "Device"
            elif arg in ['x11', 'vnc']:
                opt_gticlass = "Screen"
            else:
                error('unknown platform: "%s". Use one of "%s"' % (
                    arg, '", "'.join(supported_platforms)))

    script = ""
    if remainder:
        scriptFilename = remainder[0]
        try:
            script = file(scriptFilename).read()
        except:
            error('cannot read file "%s"' % (remainder[0],))
    else:
        scriptFilename = None

    if script:
        # script given, try connecting automatically as defined in the script
        if "import fmbt" in script:
            for line in script.split('\n'):
                if re.match("import fmbt(android|tizen|vnc|x11)", line):
                    opt_gti = line.split()[1].split(",")[0][4:]
                    log("executing: %s" % (line,))
                    exec line
                    if opt_gti in ['android', 'tizen']:
                        opt_gticlass = "Device"
                    else:
                        opt_gticlass = "Screen"
                elif re.match("\s*[a-zA-Z_].*=.*" + opt_gti + "\.(Device|Screen).*", line):
                    opt_sut = line.split("=")[0].strip()
                    log("executing: %s" % (line,))
                    exec line
                    exec "sut = " + opt_sut
    elif opt_gti == None:
        error("no platform (-p) or script, don't know how to connect")

    if opt_gti != "dummy":
        if opt_sut == None:
            initSequence = ("import fmbt%s\n"
                            "sut = fmbt%s.%s('%s')\n") % (
                                opt_gti, opt_gti, opt_gticlass, opt_connect)
            exec initSequence
            opt_sut = "sut"
    else:
        initSequence = "# sut = fmbtdummy.Device(...)\n"
        sut = fmbtdummy.Device(screenshotList = opt_connect.split(","))
        opt_sut = "sut"

    _app = QtGui.QApplication(sys.argv)
    _win = MainWindow()
    _win.resize(640, 480)
    _win.updateScreenshot()
    if script:
        _win.editor.append(script)
        _win.setFilename(scriptFilename)
    else:
        _win.editor.append(initSequence)
    _win.show()
    _app.exec_()
