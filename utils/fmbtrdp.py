# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St - Fifth Floor, Boston, MA
# 02110-1301 USA.

import ctypes
import ctypes.util

import os
import select
import string
import sys
import thread

import fmbtgti
import fmbtpng

class Device(fmbtgti.GUITestInterface):
    def __init__(self, hostport, resolution=None, connect=True):
        fmbtgti.GUITestInterface.__init__(self)
        if connect:
            self.connect(hostport, resolution)

    def connect(self, hostport, resolution=None):
        """
        Connect to RDP server

        Parameters:

          hostport (string, optional):
                  host[:port]. The default port is 3389.

          resolution (pair of integers, optional):
                  (width, height) in pixels.

        Returns True if successful, raises RdpConnectionError on error.

        Example:

          try:
              d.connect("localhost:13389", (1920, 1200))
          except fmbtrdp.RdpConnectionError, e:
              print "connection failed:", e
          else:
              d.disconnect()
        """
        self.setConnection(RDPConnection(hostport, resolution))
        return True

    def disconnect(self):
        """
        Disconnect from RDP server
        """
        c = self.connection()
        if c:
            c.close()
            self.setConnection(None)

########################################################################
# FreeRDP library binding
########################################################################

BOOL    = ctypes.c_bool
BYTE    = ctypes.c_ubyte
BYTE_P  = ctypes.POINTER(BYTE)
CHAR_P  = ctypes.c_char_p
CHAR_PP = ctypes.POINTER(ctypes.c_char_p)
DOUBLE  = ctypes.c_double
INT     = ctypes.c_int
INT_P   = ctypes.POINTER(INT)
NULL    = ctypes.c_void_p(0)
SIZE_T  = ctypes.c_size_t
UINT    = ctypes.c_uint
UINT8   = ctypes.c_int8
UINT8_P = ctypes.POINTER(UINT8)
UINT16  = ctypes.c_uint16
UINT32  = ctypes.c_uint32
UINT64  = ctypes.c_uint64
VOID_P  = ctypes.c_void_p
VOID_PP = ctypes.POINTER(VOID_P)

def _align64(field_name, field_type, offset64=None):
    rv = []
    if offset64 == None:
        offset64 = (_align64.offset8 + 7) / 8
    if _align64.offset8 < offset64 * 8:
        rv += [("_padding%s" % (str(offset64).zfill(4)),
                ctypes.c_uint8 * (offset64 * 8 - _align64.offset8))]
        _align64.offset8 = offset64 * 8
    elif _align64.offset8 > offset64 * 8:
        raise ValueError("Struct filled up to 64-bit block %s, invalid offset: %s" %
                         (_align64.offset8 / 8.0, offset64))
    rv += [(field_name, field_type)]
    _align64.offset8 += ctypes.sizeof(field_type)
    return rv

#### Colors, freerdp/codec/color.h

CLRCONV_ALPHA  = 1
CLRCONV_INVERT = 2
CLRCONV_RGB555 = 4

CLRBUF_16BPP   = 8
CLRBUF_24BPP   = 16
CLRBUF_32BPP   = 32

#### Settings, freerdp/settings.h

# Encryption Methods
ENCRYPTION_METHOD_NONE             = 0x00000000
ENCRYPTION_METHOD_40BIT            = 0x00000001
ENCRYPTION_METHOD_128BIT           = 0x00000002
ENCRYPTION_METHOD_56BIT            = 0x00000008
ENCRYPTION_METHOD_FIPS             = 0x00000010

# Encryption Levels
ENCRYPTION_LEVEL_NONE              = 0x00000000
ENCRYPTION_LEVEL_LOW               = 0x00000001
ENCRYPTION_LEVEL_CLIENT_COMPATIBLE = 0x00000002
ENCRYPTION_LEVEL_HIGH              = 0x00000003
ENCRYPTION_LEVEL_FIPS              = 0x00000004

# struct rdp_setting, incomplete, trying out basic stuff
_align64.offset8 = 0
class RdpSettings(ctypes.Structure):
    _fields_ = (
        _align64("instance",                      VOID_P) +

        # Core Parameters
        _align64("ServerMode",                    BOOL,   16) +
        _align64("ShareId",                       UINT32, 17) +
        _align64("PduSource",                     UINT32, 18) +
        _align64("ServerPort",                    UINT32, 19) +
        _align64("ServerHostname",                CHAR_P, 20) +
        _align64("Username",                      CHAR_P, 21) +
        _align64("Password",                      CHAR_P, 22) +
        _align64("Domain",                        CHAR_P, 23) +
        _align64("PasswordHash",                  CHAR_P, 24) +
        _align64("WaitForOutputBufferFlush",      BOOL,   25) +

        # Client/Server Core Data
        _align64("RdpVersion",                    UINT32, 128) +
        _align64("DesktopWidth",                  UINT32, 129) +
        _align64("DesktopHeight",                 UINT32, 130) +
        _align64("ColorDepth",                    UINT32, 131) +
        _align64("ConnectionType",                UINT32, 132) +
        _align64("ClientBuild",                   UINT32, 133) +
        _align64("ClientHostname",                CHAR_P, 134) +
        _align64("ClientProductId",               CHAR_P, 135) +
        _align64("EarlyCapabilityFlags",          UINT32, 136) +
        _align64("NetworkAutoDetect",             BOOL,   137) +
        _align64("SupportAsymetricKeys",          BOOL,   138) +
        _align64("SupportErrorInfoPdu",           BOOL,   139) +
        _align64("SupportStatusInfoPdu",          BOOL,   140) +
        _align64("SupportMonitorLayoutPdu",       BOOL,   141) +
        _align64("SupportGraphicsPipeline",       BOOL,   142) +
        _align64("SupportDynamicTimeZone",        BOOL,   143) +
        _align64("SupportHeartbeatPdu",           BOOL,   144) +

	# Client/Server Security Data
	_align64("DisableEncryption",             BOOL,   192) +
	_align64("EncryptionMethods",             UINT32, 193) +
	_align64("ExtEncryptionMethods",          UINT32, 194) +
	_align64("EncryptionLevel",               UINT32, 195) +
	_align64("ServerRandom",                  BYTE_P, 196) +
	_align64("ServerRandomLength",            UINT32, 197) +
	_align64("ServerCertificate",             BYTE_P, 198) +
	_align64("ServerCertificateLength",       UINT32, 199) +
	_align64("ClientRandom",                  BYTE_P, 200) +
	_align64("ClientRandomLength",            UINT32, 201) +

        # Protocol Security
        _align64("TlsSecurity",                   BOOL,   1088) +
        _align64("NlaSecurity",                   BOOL,   1089) +
        _align64("RdpSecurity",                   BOOL,   1090) +
        _align64("ExtSecurity",                   BOOL,   1091) +
        _align64("Authentication",                BOOL,   1092) +
        _align64("RequestedProtocols",            UINT32, 1093) +
        _align64("SelectedProtocol",              UINT32, 1094) +
        _align64("NegotiationFlags",              UINT32, 1095) +
        _align64("NegotiateSecurityLayer",        BOOL,   1096) +
        _align64("RestrictedAdminModeRequired",   BOOL,   1097) +
        _align64("AuthenticationServiceClass",    CHAR_P, 1098) +
        _align64("DisableCredentialsDelegation",  BOOL,   1099) +
        _align64("AuthenticationLevel",           BOOL,   1100) +
        _align64("PermittedTLSCiphers",           CHAR_P, 1101) +

        # Window Settings
        _align64("Workarea",                      BOOL,   1536) +
        _align64("Fullscreen",                    BOOL,   1537) +
        _align64("PercentScreen",                 UINT32, 1538) +
        _align64("GrabKeyboard",                  BOOL,   1539) +
        _align64("Decorations",                   BOOL,   1540) +
        _align64("MouseMotion",                   BOOL,   1541) +
        _align64("WindowTitle",                   CHAR_P, 1542) +
        _align64("ParentWindowId",                UINT64, 1543) +
        _align64("AsyncInput",                    BOOL,   1544) +
        _align64("AsyncUpdate",                   BOOL,   1545) +
        _align64("AsyncChannels",                 BOOL,   1546) +
        _align64("AsyncTransport",                BOOL,   1547) +
        _align64("ToggleFullscreen",              BOOL,   1548) +
        _align64("WmClass",                       CHAR_P, 1549) +
        _align64("EmbeddedWindow",                BOOL,   1550) +
        _align64("SmartSizing",                   BOOL,   1551) +
        _align64("XPan",                          INT,    1552) +
        _align64("YPan",                          INT,    1553) +
        _align64("ScalingFactor",                 DOUBLE, 1554) +

        # Input Capabilities
        _align64("KeyboardLayout",                UINT32, 2624) +
        _align64("KeyboardType",                  UINT32, 2625) +
        _align64("KeyboardSubType",               UINT32, 2626) +
        _align64("KeyboardFunctionKey",           UINT32, 2627) +
        _align64("ImeFileName",                   CHAR_P, 2628) +
        _align64("UnicodeInput",                  BOOL,   2629) +
        _align64("FastPathInput",                 BOOL,   2630) +
        _align64("MultiTouchInput",               BOOL,   2631) +
        _align64("MultiTouchGestures",            BOOL,   2632) +
        _align64("KeyboardHook",                  UINT32, 2633)
    )
RdpSettings_P = ctypes.POINTER(RdpSettings)

# Adding stuff to structs:
# query-replace-regexp
# ALIGN64 \([^ ]*\) \([^; ]*\); /\* \([0-9]*\) \*/
# ->
# _align64("\2", \1, \3) +

#### Input, freerdp/input.h

# keyboard Flags
KBD_FLAGS_EXTENDED       = 0x0100
KBD_FLAGS_DOWN           = 0x4000
KBD_FLAGS_RELEASE        = 0x8000

# Pointer Flags
PTR_FLAGS_WHEEL          = 0x0200
PTR_FLAGS_WHEEL_NEGATIVE = 0x0100
PTR_FLAGS_MOVE           = 0x0800
PTR_FLAGS_DOWN           = 0x8000
PTR_FLAGS_BUTTON1        = 0x1000
PTR_FLAGS_BUTTON2        = 0x2000
PTR_FLAGS_BUTTON3        = 0x4000
WheelRotationMask        = 0x01FF

# Extended Pointer Flags
PTR_XFLAGS_DOWN          = 0x8000
PTR_XFLAGS_BUTTON1       = 0x0001
PTR_XFLAGS_BUTTON2       = 0x0002

# Keyboard Toggle Flags
KBD_SYNC_SCROLL_LOCK     = 0x00000001
KBD_SYNC_NUM_LOCK        = 0x00000002
KBD_SYNC_CAPS_LOCK       = 0x00000004
KBD_SYNC_KANA_LOCK       = 0x00000008

RDP_CLIENT_INPUT_PDU_HEADER_LENGTH = 4

# Pointers to these structs are needed before definition of the struct

class RdpContext(ctypes.Structure):
    pass
class RdpGdi(ctypes.Structure):
    pass
class RdpInput(ctypes.Structure):
    pass
class RdpFreerdp(ctypes.Structure):
    pass

RdpContext_P = ctypes.POINTER(RdpContext)
RdpGdi_P     = ctypes.POINTER(RdpGdi)
RdpInput_P   = ctypes.POINTER(RdpInput)
RdpFreerdp_P = ctypes.POINTER(RdpFreerdp)

RdppSynchronizeEvent     = ctypes.CFUNCTYPE(None, RdpInput_P, UINT32) # input, flags
RdppKeyboardEvent        = ctypes.CFUNCTYPE(None, RdpInput_P, UINT16, UINT16) # input, flags, code
RdppUnicodeKeyboardEvent = ctypes.CFUNCTYPE(None, RdpInput_P, UINT16, UINT16) # input, flags, code
RdppMouseEvent           = ctypes.CFUNCTYPE(None, RdpInput_P, UINT16, UINT16, UINT16) # input, flags, x, y
RdppExtendedMouseEvent   = ctypes.CFUNCTYPE(None, RdpInput_P, UINT16, UINT16, UINT16) # input, flags, x, y

# struct rdp_input
_align64.offset8 = 0
RdpInput._fields_ = (
    _align64("context",               RdpContext_P) +
    _align64("param1",                VOID_P, 1) +
    _align64("SynchronizeEvent",      RdppSynchronizeEvent, 16) +
    _align64("KeyboardEvent",         RdppKeyboardEvent, 17) +
    _align64("UnicodeKeyboardEvent",  RdppUnicodeKeyboardEvent, 18) +
    _align64("MouseEvent",            RdppMouseEvent, 19) +
    _align64("ExtendedMouseEvent",    RdppExtendedMouseEvent, 20)
)

#### GDI, see freerdp/freerdp.h

# struct rdp_gdi
_align64.offset8 = 0
RdpGdi._fields_ = (
    ("context", RdpContext_P),

    ("width", INT),
    ("height", INT),
    ("dstBpp", INT),
    ("srcBpp", INT),
    ("cursor_x", INT),
    ("cursor_y", INT),
    ("bytesPerPixel", INT),

    ("hdc", VOID_P), # HGDI_DC
    ("clrconv", VOID_P), # HCLRCONV
    ("primary", VOID_P), # gdiBitmap*
    ("drawing", VOID_P), # gdiBitmap*
    ("primary_buffer", BYTE_P), # BYTE_P
    ("textColor", UINT),

    ("rfx_context", VOID_P),
    ("nsc_context", VOID_P),
    ("tile", VOID_P), # gdiBitmap*
    ("image", VOID_P) # gdiBitmap*
)

#### Core, see freerdp/freerdp.h

# struct rdp_context
_align64.offset8 = 0
RdpContext._fields_ = (
    _align64("instance",    RdpFreerdp_P, 0) +
    _align64("peer",        VOID_P, 1) + # freerdp_peer*
    _align64("ServerMode",  BOOL,   2) +
    _align64("LastError",   UINT32, 3) +

    _align64("argc",        INT,     16) +
    _align64("argv",        CHAR_PP, 17) +
    _align64("pubSub",      VOID_P,  18) + # wPubSub*

    _align64("rdp",         VOID_P,  32) + # rdpRdp*
    _align64("gdi",         RdpGdi_P, 33) +
    _align64("rail",        VOID_P,  34) + # rdpRail*
    _align64("cache",       VOID_P,  35) + # rdpCache*
    _align64("channels",    VOID_P,  36) + # rdpChannels*
    _align64("graphics",    VOID_P,  37) + # rdpGraphics*
    _align64("input",       RdpInput_P, 38) +
    _align64("update",      VOID_P,  39) + # rdpUpdate*
    _align64("settings",    RdpSettings_P, 40) +
    _align64("metrics",     VOID_P, 41) + # rdpMetrics*

    _align64("padding",     UINT64, 63) # size_of(RdpContext) will be needed
)

RdppPreConnect = ctypes.CFUNCTYPE(BOOL, RdpFreerdp_P)
RdppPostConnect = ctypes.CFUNCTYPE(BOOL, RdpFreerdp_P)
# struct rdp_freerdp
_align64.offset8 = 0
RdpFreerdp._fields_ = (
    _align64("context",                   RdpContext_P, 0) +
    _align64("pClientEntryPoints",        VOID_P) +
    _align64("input",                     RdpInput_P, 16) +
    _align64("update",                    VOID_P, 17) + # rdpUpdate*
    _align64("settings",                  RdpSettings_P, 18) +
    _align64("ContextSize",               SIZE_T, 32) +
    _align64("ContextNew",                VOID_P, 33) + # pContextNew
    _align64("ContextFree",               VOID_P, 34) + # pContextFree
    _align64("PreConnect",                RdppPreConnect, 48) +
    _align64("PostConnect",               RdppPostConnect, 49) +
    _align64("Authenticate",              VOID_P, 50) + # pAuthenticate
    _align64("VerifyCertificate",         VOID_P, 51) + # pVerifyCertificate
    _align64("VerifyChangedCertificate",  VOID_P, 52) + # pVerifyChangedCertificate
    _align64("VerifyX509Certificate",     VOID_P, 53) + # pVerifyX509Certificate
    _align64("LogonErrorInfo",            VOID_P, 54) + # pLogonErrorInfo
    _align64("PostDisconnect",            VOID_P, 55) + # pPostDisconnect
    _align64("GatewayAuthenticate",       VOID_P, 56) + # pAuthenticate
    _align64("SendChannelData",           VOID_P, 64) + # pSendChannelData
    _align64("ReceiveChannelData",        VOID_P, 65) # pReceiveChannelData
)

def _load_lib(libname):
    try:
        return ctypes.CDLL(libname)
    except OSError, e:
        raise ImportError('loading library "%s" failed: %s' % (libname, e))

libcore = _load_lib("libfreerdp-core.so.1.2")
libgdi = _load_lib("libfreerdp-gdi.so.1.2")
libutils = _load_lib("libfreerdp-utils.so.1.2")
libwinpr = _load_lib("libwinpr.so.1.1")

libcore.freerdp_new.argtypes = []
libcore.freerdp_new.restype = RdpFreerdp_P
libcore.freerdp_free.argtypes = [RdpFreerdp_P]
libcore.freerdp_free.restype = None

libcore.freerdp_connect.argtypes = [RdpFreerdp_P]
libcore.freerdp_connect.restype = BOOL
libcore.freerdp_disconnect.argtypes = [RdpFreerdp_P]
libcore.freerdp_disconnect.restype = BOOL
libcore.freerdp_channels_new.argypes = []
libcore.freerdp_channels_new.restype = VOID_P
libcore.freerdp_channels_close.argtypes = [VOID_P, RdpFreerdp_P]
libcore.freerdp_channels_close.restype = None

libcore.freerdp_context_new.argtypes = [RdpFreerdp_P]
libcore.freerdp_context_new.restype = None

libcore.freerdp_check_fds.argtypes = [RdpFreerdp_P]
libcore.freerdp_check_fds.restype = BOOL
libcore.freerdp_get_fds.argtypes = [RdpFreerdp_P, VOID_PP, INT_P, VOID_PP, INT_P]
libcore.freerdp_get_fds.restype = BOOL

libcore.freerdp_input_send_keyboard_event_ex.argtypes = [RdpInput_P, BOOL, UINT32]
libcore.freerdp_input_send_keyboard_event_ex.restype = None
libcore.freerdp_input_send_mouse_event.argtypes = [RdpInput_P, UINT16, UINT16, UINT16]
libcore.freerdp_input_send_mouse_event.restype = None

libgdi.gdi_init.argtypes = [RdpFreerdp_P, UINT32, BYTE_P]
libgdi.gdi_init.restype = INT
libgdi.gdi_free.argyptes = [RdpFreerdp_P]
libgdi.gdi_free.restype = None

libwinpr.GetVirtualScanCodeFromVirtualKeyCode.argtypes = [UINT64, UINT64]
libwinpr.GetVirtualScanCodeFromVirtualKeyCode.restype = UINT64

# End of FreeRDP library binding

# input.h
virtualKeycodes = {
    "VK_LBUTTON":                   0x01, # Left mouse button
    "VK_RBUTTON":                   0x02, # Right mouse button
    "VK_CANCEL":                    0x03, # Control-break processing
    "VK_MBUTTON":                   0x04, # Middle mouse button (three-button mouse)
    "VK_XBUTTON1":                  0x05, # Windows 2000/XP: X1 mouse button
    "VK_XBUTTON2":                  0x06, # Windows 2000/XP: X2 mouse button
    #                               0x07 is undefined
    "VK_BACK":                      0x08, # BACKSPACE key
    "VK_TAB":                       0x09, # TAB key
    #                               0x0A to 0x0B are reserved
    "VK_CLEAR":                     0x0C, # CLEAR key
    "VK_RETURN":                    0x0D, # ENTER key
    #                               0x0E to 0x0F are undefined
    "VK_SHIFT":                     0x10, # SHIFT key
    "VK_CONTROL":                   0x11, # CTRL key
    "VK_MENU":                      0x12, # ALT key
    "VK_PAUSE":                     0x13, # PAUSE key
    "VK_CAPITAL":                   0x14, # CAPS LOCK key
    "VK_KANA":                      0x15, # Input Method Editor (IME) Kana mode
    "VK_HANGUEL":                   0x15, # IME Hanguel mode (maintained for compatibility)
    "VK_HANGUL":                    0x15, # IME Hangul mode
    #                               0x16 is undefined
    "VK_JUNJA":                     0x17, # IME Junja mode
    "VK_FINAL":                     0x18, # IME final mode
    "VK_HANJA":                     0x19, # IME Hanja mode
    "VK_KANJI":                     0x19, # IME Kanji mode
    #                               0x1A is undefined
    "VK_ESCAPE":                    0x1B, # ESC key
    "VK_CONVERT":                   0x1C, # IME convert
    "VK_NONCONVERT":                0x1D, # IME nonconvert
    "VK_ACCEPT":                    0x1E, # IME accept
    "VK_MODECHANGE":                0x1F, # IME mode change request
    "VK_SPACE":                     0x20, # SPACEBAR
    "VK_PRIOR":                     0x21, # PAGE UP key
    "VK_NEXT":                      0x22, # PAGE DOWN key
    "VK_END":                       0x23, # END key
    "VK_HOME":                      0x24, # HOME key
    "VK_LEFT":                      0x25, # LEFT ARROW key
    "VK_UP":                        0x26, # UP ARROW key
    "VK_RIGHT":                     0x27, # RIGHT ARROW key
    "VK_DOWN":                      0x28, # DOWN ARROW key
    "VK_SELECT":                    0x29, # SELECT key
    "VK_PRINT":                     0x2A, # PRINT key
    "VK_EXECUTE":                   0x2B, # EXECUTE key
    "VK_SNAPSHOT":                  0x2C, # PRINT SCREEN key
    "VK_INSERT":                    0x2D, # INS key
    "VK_DELETE":                    0x2E, # DEL key
    "VK_HELP":                      0x2F, # HELP key
    # Digits, the last 4 bits of the code represent the corresponding digit
    "VK_KEY_0":                     0x30, # '0' key
    "VK_KEY_1":                     0x31, # '1' key
    "VK_KEY_2":                     0x32, # '2' key
    "VK_KEY_3":                     0x33, # '3' key
    "VK_KEY_4":                     0x34, # '4' key
    "VK_KEY_5":                     0x35, # '5' key
    "VK_KEY_6":                     0x36, # '6' key
    "VK_KEY_7":                     0x37, # '7' key
    "VK_KEY_8":                     0x38, # '8' key
    "VK_KEY_9":                     0x39, # '9' key
    #                               0x3A to 0x40 are undefined
    # The alphabet, the code corresponds to the capitalized letter in the ASCII code
    "VK_KEY_A":                     0x41, # 'A' key
    "VK_KEY_B":                     0x42, # 'B' key
    "VK_KEY_C":                     0x43, # 'C' key
    "VK_KEY_D":                     0x44, # 'D' key
    "VK_KEY_E":                     0x45, # 'E' key
    "VK_KEY_F":                     0x46, # 'F' key
    "VK_KEY_G":                     0x47, # 'G' key
    "VK_KEY_H":                     0x48, # 'H' key
    "VK_KEY_I":                     0x49, # 'I' key
    "VK_KEY_J":                     0x4A, # 'J' key
    "VK_KEY_K":                     0x4B, # 'K' key
    "VK_KEY_L":                     0x4C, # 'L' key
    "VK_KEY_M":                     0x4D, # 'M' key
    "VK_KEY_N":                     0x4E, # 'N' key
    "VK_KEY_O":                     0x4F, # 'O' key
    "VK_KEY_P":                     0x50, # 'P' key
    "VK_KEY_Q":                     0x51, # 'Q' key
    "VK_KEY_R":                     0x52, # 'R' key
    "VK_KEY_S":                     0x53, # 'S' key
    "VK_KEY_T":                     0x54, # 'T' key
    "VK_KEY_U":                     0x55, # 'U' key
    "VK_KEY_V":                     0x56, # 'V' key
    "VK_KEY_W":                     0x57, # 'W' key
    "VK_KEY_X":                     0x58, # 'X' key
    "VK_KEY_Y":                     0x59, # 'Y' key
    "VK_KEY_Z":                     0x5A, # 'Z' key
    "VK_LWIN":                      0x5B, # Left Windows key (Microsoft Natural keyboard)
    "VK_RWIN":                      0x5C, # Right Windows key (Natural keyboard)
    "VK_APPS":                      0x5D, # Applications key (Natural keyboard)
    #                               0x5E is reserved
    "VK_POWER":                     0x5E, # Power key
    "VK_SLEEP":                     0x5F, # Computer Sleep key
    # Numeric keypad digits, the last four bits of the code represent the corresponding digit
    "VK_NUMPAD0":                   0x60, # Numeric keypad '0' key
    "VK_NUMPAD1":                   0x61, # Numeric keypad '1' key
    "VK_NUMPAD2":                   0x62, # Numeric keypad '2' key
    "VK_NUMPAD3":                   0x63, # Numeric keypad '3' key
    "VK_NUMPAD4":                   0x64, # Numeric keypad '4' key
    "VK_NUMPAD5":                   0x65, # Numeric keypad '5' key
    "VK_NUMPAD6":                   0x66, # Numeric keypad '6' key
    "VK_NUMPAD7":                   0x67, # Numeric keypad '7' key
    "VK_NUMPAD8":                   0x68, # Numeric keypad '8' key
    "VK_NUMPAD9":                   0x69, # Numeric keypad '9' key
    # Numeric keypad operators and special keys
    "VK_MULTIPLY":                  0x6A, # Multiply key
    "VK_ADD":                       0x6B, # Add key
    "VK_SEPARATOR":                 0x6C, # Separator key
    "VK_SUBTRACT":                  0x6D, # Subtract key
    "VK_DECIMAL":                   0x6E, # Decimal key
    "VK_DIVIDE":                    0x6F, # Divide key
    # Function keys, from F1 to F24
    "VK_F1":                        0x70, # F1 key
    "VK_F2":                        0x71, # F2 key
    "VK_F3":                        0x72, # F3 key
    "VK_F4":                        0x73, # F4 key
    "VK_F5":                        0x74, # F5 key
    "VK_F6":                        0x75, # F6 key
    "VK_F7":                        0x76, # F7 key
    "VK_F8":                        0x77, # F8 key
    "VK_F9":                        0x78, # F9 key
    "VK_F10":                       0x79, # F10 key
    "VK_F11":                       0x7A, # F11 key
    "VK_F12":                       0x7B, # F12 key
    "VK_F13":                       0x7C, # F13 key
    "VK_F14":                       0x7D, # F14 key
    "VK_F15":                       0x7E, # F15 key
    "VK_F16":                       0x7F, # F16 key
    "VK_F17":                       0x80, # F17 key
    "VK_F18":                       0x81, # F18 key
    "VK_F19":                       0x82, # F19 key
    "VK_F20":                       0x83, # F20 key
    "VK_F21":                       0x84, # F21 key
    "VK_F22":                       0x85, # F22 key
    "VK_F23":                       0x86, # F23 key
    "VK_F24":                       0x87, # F24 key
    #                               0x88 to 0x8F are unassigned
    "VK_NUMLOCK":                   0x90, # NUM LOCK key
    "VK_SCROLL":                    0x91, # SCROLL LOCK key
    #                               0x92 to 0x96 are OEM specific
    #                               0x97 to 0x9F are unassigned
    # Modifier keys
    "VK_LSHIFT":                    0xA0, # Left SHIFT key
    "VK_RSHIFT":                    0xA1, # Right SHIFT key
    "VK_LCONTROL":                  0xA2, # Left CONTROL key
    "VK_RCONTROL":                  0xA3, # Right CONTROL key
    "VK_LMENU":                     0xA4, # Left MENU key
    "VK_RMENU":                     0xA5, # Right MENU key
    # Browser related keys
    "VK_BROWSER_BACK":              0xA6, # Windows 2000/XP: Browser Back key
    "VK_BROWSER_FORWARD":           0xA7, # Windows 2000/XP: Browser Forward key
    "VK_BROWSER_REFRESH":           0xA8, # Windows 2000/XP: Browser Refresh key
    "VK_BROWSER_STOP":              0xA9, # Windows 2000/XP: Browser Stop key
    "VK_BROWSER_SEARCH":            0xAA, # Windows 2000/XP: Browser Search key
    "VK_BROWSER_FAVORITES":         0xAB, # Windows 2000/XP: Browser Favorites key
    "VK_BROWSER_HOME":              0xAC, # Windows 2000/XP: Browser Start and Home key
    # Volume related keys
    "VK_VOLUME_MUTE":               0xAD, # Windows 2000/XP: Volume Mute key
    "VK_VOLUME_DOWN":               0xAE, # Windows 2000/XP: Volume Down key
    "VK_VOLUME_UP":                 0xAF, # Windows 2000/XP: Volume Up key
    # Media player related keys
    "VK_MEDIA_NEXT_TRACK":          0xB0, # Windows 2000/XP: Next Track key
    "VK_MEDIA_PREV_TRACK":          0xB1, # Windows 2000/XP: Previous Track key
    "VK_MEDIA_STOP":                0xB2, # Windows 2000/XP: Stop Media key
    "VK_MEDIA_PLAY_PAUSE":          0xB3, # Windows 2000/XP: Play/Pause Media key
    # Application launcher keys
    "VK_LAUNCH_MAIL":               0xB4, # Windows 2000/XP: Start Mail key
    "VK_MEDIA_SELECT":              0xB5, # Windows 2000/XP: Select Media key
    "VK_LAUNCH_MEDIA_SELECT":       0xB5, # Windows 2000/XP: Select Media key
    "VK_LAUNCH_APP1":               0xB6, # Windows 2000/XP: Start Application 1 key
    "VK_LAUNCH_APP2":               0xB7, # Windows 2000/XP: Start Application 2 key
    #                               0xB8 and 0xB9 are reserved
    # OEM keys
    "VK_OEM_1":                     0xBA,
    "VK_OEM_PLUS":                  0xBB,
    "VK_OEM_COMMA":                 0xBC,
    "VK_OEM_MINUS":                 0xBD,
    "VK_OEM_PERIOD":                0xBE,
    "VK_OEM_2":                     0xBF,
    "VK_OEM_3":                     0xC0,
    #                               0xC1 to 0xD7 are reserved
    "VK_ABNT_C1":                   0xC1, # Brazilian (ABNT) Keyboard
    "VK_ABNT_C2":                   0xC2, # Brazilian (ABNT) Keyboard
    #                               0xD8 to 0xDA are unassigned
    "VK_OEM_4":                     0xDB,
    "VK_OEM_5":                     0xDC,
    "VK_OEM_6":                     0xDD,
    "VK_OEM_7":                     0xDE,
    "VK_OEM_8":                     0xDF, # Used for miscellaneous characters; it can vary by keyboard.
    #                               0xE0 is reserved
    "VK_OEM_AX":                    0xE1, # AX key on Japanese AX keyboard
    "VK_OEM_1                       02": 0xE2,
    #                               0xE3 and 0xE4 are OEM specific
    "VK_PROCESSKEY":                0xE5,
    #                               0xE6 is OEM specific
    "VK_PACKET":                    0xE7,
    #                               0xE8 is unassigned
    #                               0xE9 to 0xF5 are OEM specific
    "VK_OEM_RESET":                 0xE9,
    "VK_OEM_JUMP":                  0xEA,
    "VK_OEM_PA1":                   0xEB,
    "VK_OEM_PA2":                   0xEC,
    "VK_OEM_PA3":                   0xED,
    "VK_OEM_WSCTRL":                0xEE,
    "VK_OEM_CUSEL":                 0xEF,
    "VK_OEM_ATTN":                  0xF0,
    "VK_OEM_FINISH":                0xF1,
    "VK_OEM_COPY":                  0xF2,
    "VK_OEM_AUTO":                  0xF3,
    "VK_OEM_ENLW":                  0xF4,
    "VK_OEM_BACKTAB":               0xF5,
    "VK_ATTN":                      0xF6, # Attn key
    "VK_CRSEL":                     0xF7, # CrSel key
    "VK_EXSEL":                     0xF8, # ExSel key
    "VK_EREOF":                     0xF9, # Erase EOF key
    "VK_PLAY":                      0xFA, # Play key
    "VK_ZOOM":                      0xFB, # Zoom key
    "VK_NONAME":                    0xFC, # Reserved
    "VK_PA1":                       0xFD, # PA1 key
    "VK_OEM_CLEAR":                 0xFE, # Clear key
    "VK_NONE":                      0xFF, # no key
    "VK_DBE_ALPHANUMERIC":          0xF0, # Changes the mode to alphanumeric.
    "VK_DBE_KATAKANA":              0xF1, # Changes the mode to Katakana.
    "VK_DBE_HIRAGANA":              0xF2, # Changes the mode to Hiragana.
    "VK_DBE_SBCSCHAR":              0xF3, # Changes the mode to single-byte characters.
    "VK_DBE_DBCSCHAR":              0xF4, # Changes the mode to double-byte characters.
    "VK_DBE_ROMAN":                 0xF5, # Changes the mode to Roman characters.
    "VK_DBE_NOROMAN":               0xF6, # Changes the mode to non-Roman characters.
    "VK_DBE_ENTERWORDREGISTERMODE": 0xF7, # Activates the word registration dialog box.
    "VK_DBE_ENTERIMECONFIGMODE":    0xF8, # Activates a dialog box for setting up an IME environment.
    "VK_DBE_FLUSHSTRING":           0xF9, # Deletes the undetermined string without determining it.
    "VK_DBE_CODEINPUT":             0xFA, # Changes the mode to code input.
    "VK_DBE_NOCODEINPUT":           0xFB  # Changes the mode to no-code input.
}
# end of input.h

_usKbLayoutChars = {
    '\n': ("VK_RETURN", []),
    ' ': ("VK_SPACE", []),
    '`': ("VK_OEM_5", []),      '~': ("VK_OEM_5", ["VK_LSHIFT"]),
    '!': ("VK_KEY_1", ["VK_LSHIFT"]),
    '@': ("VK_KEY_2", ["VK_LSHIFT"]),
    '#': ("VK_KEY_3", ["VK_LSHIFT"]),
    '$': ("VK_KEY_4", ["VK_LSHIFT"]),
    '%': ("VK_KEY_5", ["VK_LSHIFT"]),
    '^': ("VK_KEY_6", ["VK_LSHIFT"]),
    '&': ("VK_KEY_7", ["VK_LSHIFT"]),
    '*': ("VK_KEY_8", ["VK_LSHIFT"]),
    '(': ("VK_KEY_9", ["VK_LSHIFT"]),
    ')': ("VK_KEY_0", ["VK_LSHIFT"]),
    '-': ("VK_OEM_MINUS", []),  '_': ("VK_OEM_MINUS", ["VK_LSHIFT"]),
    '=': ("VK_OEM_PLUS", []),   '+': ("VK_OEM_PLUS", ["VK_LSHIFT"]),
    '\t': ("VK_TAB", []),
    '[': ("VK_OEM_4", []),      '{': ("VK_OEM_4", ["VK_LSHIFT"]),
    ']': ("VK_OEM_6", []),      '}': ("VK_OEM_6", ["VK_LSHIFT"]),
    ';': ("VK_OEM_1", []),      ':': ("VK_OEM_1", ["VK_LSHIFT"]),
    "'": ("VK_OEM_7", []),      '"': ("VK_OEM_7", ["VK_LSHIFT"]),
    '\\': ("VK_OEM_5", []),     '|': ("VK_OEM_5", ["VK_LSHIFT"]),
    ',': ("VK_OEM_COMMA", []),  '<': ("VK_OEM_COMMA", ["VK_LSHIFT"]),
    '.': ("VK_OEM_PERIOD", []), '>': ("VK_OEM_PERIOD", ["VK_LSHIFT"]),
    '/': ("VK_OEM_2", []),      '?': ("VK_OEM_2", ["VK_LSHIFT"])
}

def _keyToScancode(keyNameOrCode):
    keycode = virtualKeycodes.get(keyNameOrCode, keyNameOrCode)
    if not isinstance(keycode, int):
        raise ValueError('invalid key "%s"' % (keyName,))
    scancode = libwinpr.GetVirtualScanCodeFromVirtualKeyCode(keycode, 4)
    return scancode

def _preConnect(instance_p):
    return True

def _postConnect(instance_p):
    rv = libgdi.gdi_init(instance_p,
                         CLRCONV_ALPHA | CLRCONV_INVERT | CLRBUF_16BPP | CLRBUF_32BPP,
                         ctypes.cast(NULL, BYTE_P))
    return True

class RDPConnection(fmbtgti.GUITestConnection):
    def __init__(self, hostport, resolution=None, connect=True):
        fmbtgti.GUITestConnection.__init__(self)
        self.instance = None
        self._hostport = hostport
        self._resolution = resolution
        self._connectionError = None
        if connect and not self.connect(hostport, resolution):
            raise RdpConnectionError('connecting to "%s" failed' % (hostport,))

    def connect(self, hostport=None, resolution=None):
        if hostport:
            self._hostport = hostport
        else:
            hostport = self._hostport

        if resolution:
            self._resolution = resolution
        else:
            resolution = self._resolution

        self._connectionError = None

        if ":" in hostport:
            try:
                self.host, port = hostport.split(":", 1)
                self.port = int(port)
            except ValueError:
                raise RdpConnectionError('invalid hostport (host[:port]) "%s"' % (hostport,))
        else:
            self.host = hostport
            self.port = 3389

        self.instance_p = libcore.freerdp_new()
        self.instance = self.instance_p.contents

        self.instance.PreConnect = RdppPreConnect(_preConnect)
        self.instance.PostConnect = RdppPostConnect(_postConnect)
        self.instance.VerifyCertificate = NULL
        self.instance.ReceiveChannelData = NULL

        self.instance.ContextNew = NULL
        self.instance.ContextFree = NULL

        libcore.freerdp_context_new(self.instance_p)

        self.context = self.instance.context.contents
        self.context.channels = libcore.freerdp_channels_new()

        self.settings = self.instance.settings.contents
        self.settings.RdpSecurity = True
        self.settings.TlsSecurity = False
        self.settings.NlaSecurity = False
        self.settings.ServerHostname = self.host
        self.settings.ServerPort = self.port
        self.settings.DisableEncryption = True

        self.settings.ColorDepth = 32
        self.settings.Workarea = False
        if resolution:
            width, height = resolution
            self.settings.DesktopWidth = width
            self.settings.DesktopHeight = height

        if libcore.freerdp_connect(self.instance_p):
            self._rfds = (VOID_P * 256)(0)
            self._wfds = (VOID_P * 256)(0)
            self._thread_lock = thread.allocate_lock()
            self._pipe_rfd, self._pipe_wfd = os.pipe()
            thread.start_new_thread(self._communication, ())
            return True
        else:
            return False

    def close(self):
        if self.instance:
            libcore.freerdp_channels_close(self.context.channels, self.instance_p)
            libcore.freerdp_channels_free(self.context.channels)
            libgdi.gdi_free(self.instance_p)
            libcore.freerdp_disconnect(self.instance_p)
            libcore.freerdp_free(self.instance_p)

    def error(self):
        rv = self._connectionError
        self._connectionError = None
        return rv

    def recvScreenshot(self, filename):
        gdi = self.context.gdi.contents
        w = gdi.width
        h = gdi.height

        with self._thread_lock:
            png_data = fmbtpng.raw2png(gdi.primary_buffer, w, h, fmt="RGBA")

        file(filename, "wb").write(png_data)
        return True

    def sendKeyDown(self, keyName, modifiers=[]):
        if modifiers:
            self.sendKeyDown(modifiers[0])
            try:
                self.sendKeyDown(keyName, modifiers[1:])
            finally:
                self.sendKeyUp(modifiers[0])
        else:
            scancode = _keyToScancode(keyName)
            libcore.freerdp_input_send_keyboard_event_ex(self.instance.input, True, scancode)
        return True

    def sendKeyUp(self, keyName, modifiers=[]):
        if modifiers:
            self.sendKeyDown(modifiers[0])
            try:
                self.sendKeyUp(keyName, modifiers[1:])
            finally:
                self.sendKeyUp(modifiers[0])
        else:
            scancode = _keyToScancode(keyName)
            libcore.freerdp_input_send_keyboard_event_ex(self.instance.input, False, scancode)
        return True

    def sendPress(self, keyName, modifiers=[]):
        for modKey in modifiers:
            self.sendKeyDown(modKey)
        self.sendKeyDown(keyName)
        self.sendKeyUp(keyName)
        for modKey in reversed(modifiers):
            self.sendKeyUp(modKey)
        return True

    def sendType(self, text):
        for char in text:
            if char in string.lowercase or char in string.digits:
                self.sendPress("VK_KEY_" + char.upper())
            elif char in string.uppercase:
                self.sendPress("VK_KEY_" + char, modifiers=["VK_LSHIFT"])
            elif char in _usKbLayoutChars:
                keyName, modifiers = _usKbLayoutChars[char]
                self.sendPress(keyName, modifiers)

    def sendTouchDown(self, x, y):
        flags = UINT16(PTR_FLAGS_BUTTON1 | PTR_FLAGS_DOWN)
        libcore.freerdp_input_send_mouse_event(self.instance.input, flags, x, y)
        return True

    def sendTouchUp(self, x, y):
        flags = UINT16(PTR_FLAGS_BUTTON1)
        libcore.freerdp_input_send_mouse_event(self.instance.input, flags, x, y)
        return True

    def _communication(self):
        # This method runs in a separate thread.
        # It takes care of I/O between the RDP server.
        rv = None

        self._rfds[0] = self._pipe_rfd

        try:
            while True:
                rfd_count = ctypes.c_int(1)
                wfd_count = ctypes.c_int(0)
                if not (libcore.freerdp_get_fds(
                        self.instance_p,
                        self._rfds, ctypes.pointer(rfd_count),
                        self._wfds, ctypes.pointer(wfd_count))):
                    raise RdpConnectionError("no file descriptors available for reading")

                int_rfds = [fd if fd else 0 for fd in self._rfds[:rfd_count.value]]
                rfds, _, _ = select.select(int_rfds, [], [])

                if self._pipe_rfd in rfds:
                    # communication from the main thread
                    msg = os.read(self._pipe_rfd, 1)


                with self._thread_lock:
                    if not libcore.freerdp_check_fds(self.instance_p):
                        raise RdpConnectionError("checking fds failed")


        except Exception, e:
            self._connectionError = RdpConnectionError("connection lost: %s", e)

    def __del__(self):
        self.close()

class RdpConnectionError(Exception):
    pass
