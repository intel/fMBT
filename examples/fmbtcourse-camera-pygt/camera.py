# camera.py

# This is the "camera implementation" to be tested in this example.

import time

g_capturedPreviewFrames = 0
g_capturingVideo = False

def capture(params):
    if not g_capturingVideo:
        time.sleep(1)
        file(params['photo'],"a").write('camera.capture\n')

def startPreview(params):
    global g_capturedPreviewFrames
    if g_capturingVideo:
        g_capturedPreviewFrames += 15
    else:
        g_capturedPreviewFrames += 25

def stopPreview():
    global g_capturedPreviewFrames
    g_capturedPreviewFrames = 0
    pass

def previewing():
    return g_capturedPreviewFrames != 0

def previewFrameCount():
    return g_capturedPreviewFrames

def startVideoCapture():
    global g_capturingVideo
    g_capturingVideo = True

def stopVideoCapture():
    global g_capturingVideo
    g_capturingVideo = False
