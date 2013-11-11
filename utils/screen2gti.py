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
import sys
import time

def error(msg, exitStatus=1):
    sys.stderr.write("screen2gti: %s\n" % (msg,))
    sys.exit(1)

def debug(msg, debugLevel=1):
    if opt_debug >= debugLevel:
        sys.stderr.write("screen2gti debug: %s\n" % (msg,))


def quantify(item, quantum):
    if not isinstance(item, tuple) and not isinstance(item, list):
        return int(item * (1/quantum)) * quantum
    else:
        return tuple([int(i * (1/quantum)) * quantum for i in item])

def gestureToGti(gestureEventList):
    timeQuantum = 0.1 # seconds
    locQuantum = 0.025 # 1.0 = full display height/width
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
    def changeScale(self, coefficient):
        self.attrowner.wheel_scale *= coefficient
        if self.attrowner.wheel_scale < self.min_scale: self.attrowner.wheel_scale = self.min_scale
        elif self.attrowner.wheel_scale > self.max_scale: self.attrowner.wheel_scale = self.max_scale
        self.attrowner.wheel_scale_changed()
    def eventFilter(self, obj, event):
        def posToRel(pos):
            sbY = self.attrowner.verticalScrollBar().value()
            sbX = self.attrowner.horizontalScrollBar().value()
            wS = self.attrowner.wheel_scale
            x = (pos().x() + sbX) / wS / float(self.mainwindow.screenshotImage.width())
            y = (pos().y() + sbY) / wS / float(self.mainwindow.screenshotImage.height())
            return (x, y)
        if event.type() == QtCore.QEvent.MouseMove:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mousemove", None, posToRel(event.pos)))
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if not self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = True
                self.mainwindow.gestureEvents = [
                    GestureEvent("mousedown", 0, posToRel(event.pos))]
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = False
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mouseup", 0, posToRel(event.pos)))
                s = gestureToGti(self.mainwindow.gestureEvents)
                cmd = "sut" + s
                self.mainwindow.gestureEvents = []
                if self.mainwindow.screenshotButtonInteract.isChecked():
                    debug("sending command %s" % (cmd,))
                    eval(cmd)
                    QtCore.QTimer.singleShot(1000, self.mainwindow.updateScreenshot)
                else:
                    debug("dropping command %s" % (cmd,))
                if self.mainwindow.editorButtonRec.isChecked():
                    self.mainwindow.editor.insertPlainText(cmd + "\n")
        elif event.type() == QtCore.QEvent.ToolTip:
            if not hasattr(self.attrowner, 'cursorForPosition'):
                return False
            cursor = self.attrowner.cursorForPosition(event.pos())
            pos = cursor.positionInBlock()
            lineno = cursor.blockNumber()
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            l = cursor.selectedText()
            start = l.rfind('"', 0, pos)
            end = l.find('"', pos)
            if -1 < start < end:
                quotedString = l[start+1:end]
                if self.visibleTip == (lineno, quotedString):
                    return True
                QtGui.QToolTip.hideText()
                if quotedString.lower().rsplit(".")[-1] in ["png", "jpg"]:
                    # tooltip for an image file
                    filename = quotedString
                    path = ':'.join([s.strip() for s in GT_IMAGEPATHRE.findall(self.mainwindow._modelSources())])
                    for d in path.split(':'):
                        filepath = os.path.join(d, filename)
                        if os.access(filepath, os.R_OK):
                            QtGui.QToolTip.showText(event.globalPos(), '%s<br><img src="%s">' % (filepath, filepath))
                            break
                    else:
                        QtGui.QToolTip.showText(event.globalPos(), '%s<br>not in found in<br># preview-image-path:...' % (filename,))
                    self.visibleTip = (lineno, quotedString)
            else:
                self.visibleTip = None
                QtGui.QToolTip.hideText()
            return True

        if event.type() == QtCore.QEvent.Wheel and event.modifiers() == QtCore.Qt.ControlModifier:
            coefficient = 1.0 + event.delta() / 1440.0
            self.changeScale(coefficient)
        return False


class fmbtdummy(object):
    class Device(object):
        def __init__(self, screenshotList=[]):
            self.scl = screenshotList
        def refreshScreenshot(self):
            s = fmbtgti.Screenshot(screenshotFile=self.scl[0])
            self.scl.append(self.scl.pop(0)) # rotate screenshots
            return s
        def __getattr__(self, name):
            def argPrinter(*args, **kwargs):
                a = []
                for arg in args:
                    a.append(repr(arg))
                for k, v in kwargs.iteritems():
                    a.append('%s=%s' % (k, repr(v)))
                print "dummy.%s(%s)" % (name, ", ".join(a))
            return argPrinter

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

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
                                                         text="Refresh")
        self.screenshotButtonsL.addWidget(self.screenshotButtonRefresh)
        self.screenshotButtonInteract = QtGui.QPushButton(self.screenshotButtons,
                                                        text="Control",
                                                        checkable = True)
        self.screenshotButtonsL.addWidget(self.screenshotButtonInteract)
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
        self.editorButtonRunAll = QtGui.QPushButton("Run all")
        self.editorButtonsLayout.addWidget(self.editorButtonRec)
        self.editorButtonsLayout.addWidget(self.editorButtonRunSingle)
        self.editorButtonsLayout.addWidget(self.editorButtonRunAll)
        self.editorWidgetsLayout.addWidget(self.editorButtons)

        self.editor = QtGui.QTextEdit()
        self.editorWidgetsLayout.addWidget(self.editor)
        self.splitter.addWidget(self.editorWidgets)

        self.setCentralWidget(self.mainwidget)

        ### Menus
        fileMenu = QtGui.QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)
        fileMenu.addAction("E&xit", QtGui.qApp.quit, "Ctrl+Q")

        self.gestureEvents = []
        self.gestureStarted = False

    def updateScreenshot(self):
        sut.refreshScreenshot().save("screen2gti.png")
        self.screenshotImage = QtGui.QImage()
        self.screenshotImage.load("screen2gti.png")
        self.screenshotQLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                self.screenshotImage))
        self.screenshotContainer.area.setWidget(self.screenshotQLabel)
        self.screenshotContainer.area.wheel_scale_changed()

if __name__ == "__main__":

    opt_connect = ""
    opt_gti = None
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

    if opt_gti == None:
        error("no platform specified (-p)")

    if opt_gti != "dummy":
        initSequence = ("import fmbt%s\n"
                        "sut = fmbt%s.%s('%s')\n") % (
            opt_gti, opt_gti, opt_gticlass, opt_connect)
        exec initSequence
        """
        l = __import__("fmbt" + opt_gti)
        cmd = "l.%s('%s')" % (opt_gticlass, opt_connect)
        print cmd
        gti = eval(cmd)
        """
    else:
        initSequence = "# sut = fmbtdummy.Device(...)\n"
        sut = fmbtdummy.Device(screenshotList = opt_connect.split(","))

    _app = QtGui.QApplication(sys.argv)
    _win = MainWindow()
    _win.resize(640, 480)
    _win.updateScreenshot()
    _win.editor.append(initSequence)
    _win.show()
    _app.exec_()
