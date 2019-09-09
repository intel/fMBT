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

# Converts raw images into PNG, based on libpng.

import ctypes
import os

try:
    import fmbt3gti
except ImportError:
    fmbtgti = None

PNG_MAGIC = "\x89PNG\x0d\x0a\x1a\x0a"
PNG_HEADER_VERSION_STRING = None
PNG_LIBPNG_VERSION_STRING = None
PNG_COLOR_MASK_COLOR = 2
PNG_COLOR_MASK_ALPHA = 4
PNG_COLOR_TYPE_RGB = PNG_COLOR_MASK_COLOR
PNG_COLOR_TYPE_RGB_ALPHA = PNG_COLOR_MASK_COLOR | PNG_COLOR_MASK_ALPHA
PNG_INTERLACE_NONE = 0
PNG_COMPRESSION_TYPE_DEFAULT = 0
PNG_FILTER_TYPE_DEFAULT = 0
PNG_TRANSFORM_IDENTITY = 0

NULL = ctypes.c_void_p(0)

if os.name == "nt":
    libpng_filenames = ["libpng16-16.dll"]
else:
    libpng_filenames = ["libpng.so", "libpng12.so.0", "libpng15.so.15",
                        "libpng16.so.16"]

libpng = None
for libpng_filename in libpng_filenames:
    try:
        libpng = ctypes.CDLL(libpng_filename)
        break
    except OSError:
        continue
if libpng == None:
    raise ImportError("loading libpng.so failed")

libpng.png_create_write_struct.restype = ctypes.c_void_p
libpng.png_create_write_struct.argtypes = [
    ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

libpng.png_get_header_ver.restype = ctypes.c_char_p
libpng.png_get_header_ver.argtypes = [ctypes.c_void_p]

libpng.png_create_info_struct.restype = ctypes.c_void_p
libpng.png_create_info_struct.argtypes = [ctypes.c_void_p]

libpng.png_set_write_fn.restype = None
libpng.png_set_write_fn.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

libpng.png_set_rows.restype = None
libpng.png_set_rows.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

libpng.png_set_IHDR.restype = None
libpng.png_set_IHDR.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

libpng.png_write_png.restype = None
libpng.png_write_png.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

PNG_LIBPNG_VERSION_STRING = libpng.png_get_header_ver(None)

def raw2png(data, width, height, depth=8, fmt="RGB"):
    """convert raw image into PNG

    Parameters:
      data (string or a ctypes pointer type):
              image data

      width (integer):
              width of the image in pixels

      height (integer):
              height of the image in pixels

      depth (integer, optional):
              color depth, bits per color channel.
              The default is 8 (that is, RGB has 24 bpp, RGBA 32 bpp).

      fmt (string, optional):
              image data format. The default is "RGB".
              Supported formats: "RGB", "RGBA", "RGB_", "BGR", "BGR_".

    Returns string that contains PNG image data.

    Example: create a png image with one half-opaque green pixel
      png_data = raw2png("\x00\xff\x00\x80", 1, 1, fmt="RGBA")
      file("green.png", "wb").write(png_data)
    """
    png_data = []

    png_struct = ctypes.c_void_p(
        libpng.png_create_write_struct(PNG_LIBPNG_VERSION_STRING,
                                       NULL, NULL, NULL))

    if not png_struct:
        raise PngError("png_create_write_struct failed")

    info_struct = ctypes.c_void_p(
        libpng.png_create_info_struct(png_struct))
    if not info_struct:
        libpng.png_destroy_write_struct(png_struct, ctypes.c_void_p(0))
        raise PngError("png_create_info_struct failed")

    def cb_png_write(png_struct, data, datalen):
        png_data.append(ctypes.string_at(data, datalen))
    c_cb_png_write = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_size_t)(cb_png_write)

    libpng.png_set_write_fn(png_struct, NULL, c_cb_png_write, NULL)

    if isinstance(data, (str, bytes)):
        buf = ctypes.c_buffer(data)
    else:
        buf = data.contents

    fmt = fmt.upper()
    if fmt == "RGB":
        color_type = PNG_COLOR_TYPE_RGB
        bytes_per_pixel = (depth // 8) * 3
    elif fmt == "RGB565":
        color_type = PNG_COLOR_TYPE_RGB
        bytes_per_pixel = 3
        depth = 8
        orig_buf = buf
        buf = ctypes.create_string_buffer(width * height * bytes_per_pixel)
        fmbtgti.eye4graphics.rgb5652rgb(orig_buf, width, height, buf)
    elif fmt == "RGBA":
        color_type = PNG_COLOR_TYPE_RGB_ALPHA
        bytes_per_pixel = (depth // 8) * 4
    elif fmt == "RGB_" and fmbtgti:
        fmbtgti.eye4graphics.rgbx2rgb(buf, width, height)
        color_type = PNG_COLOR_TYPE_RGB
        bytes_per_pixel = (depth // 8) * 3
    elif fmt == "BGR" and fmbtgti:
        fmbtgti.eye4graphics.bgr2rgb(buf, width, height)
        color_type = PNG_COLOR_TYPE_RGB
        bytes_per_pixel = (depth // 8) * 3
    elif fmt == "BGR_" and fmbtgti:
        fmbtgti.eye4graphics.bgrx2rgb(buf, width, height)
        color_type = PNG_COLOR_TYPE_RGB
        bytes_per_pixel = (depth // 8) * 3
    else:
        raise ValueError('Unsupported data format "%s", use "RGB" or "RGBA"')

    buf_addr = ctypes.addressof(buf)

    libpng.png_set_IHDR(
        png_struct, info_struct, width, height, depth,
        color_type, PNG_INTERLACE_NONE,
        PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT)

    rows = (ctypes.c_void_p * height)()
    bytes_per_row = width * bytes_per_pixel
    for row in range(height):
        rows[row] = buf_addr
        buf_addr += bytes_per_row

    libpng.png_set_rows(png_struct, info_struct, rows)
    libpng.png_write_png(png_struct, info_struct, PNG_TRANSFORM_IDENTITY, NULL)

    png_structp = ctypes.POINTER(ctypes.c_void_p)(png_struct)
    png_infop = ctypes.POINTER(ctypes.c_void_p)(info_struct)

    libpng.png_destroy_write_struct(png_structp, png_infop)

    return b"".join(png_data)

class PngError(Exception):
    pass

if __name__ == "__main__":
    png_data = raw2png(
        b"\xff\x00\x00\x80\x00\x00\x40\x00\x00\x20\x00\x00"
        b"\x00\xff\x00\x00\x80\x00\x00\x40\x00\x00\x20\x00"
        b"\x00\x00\xff\x00\x00\x80\x00\x00\x40\x00\x00\x20",
        4, 3, 8, "rgb")
    open("fmbtpng-test.png", "wb").write(png_data)
