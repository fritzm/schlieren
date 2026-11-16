"""Encoders for the thumbnail image formats: 8-bit RGBA PNG and QOI, from an (height, width, 4) uint8 array."""

import struct
import zlib

import numpy as np

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_COLOR_TYPE_RGBA = 6

QOI_MAGIC = b"qoif"
QOI_CHANNELS_RGBA = 4
QOI_COLORSPACE_SRGB = 0
QOI_END = b"\x00\x00\x00\x00\x00\x00\x00\x01"
QOI_OP_INDEX, QOI_OP_DIFF, QOI_OP_LUMA, QOI_OP_RUN = 0x00, 0x40, 0x80, 0xC0
QOI_OP_RGB, QOI_OP_RGBA = 0xFE, 0xFF
QOI_MAX_RUN = 62


def _check(pixels: np.ndarray) -> None:
    if pixels.ndim != 3 or pixels.shape[2] != 4 or pixels.dtype != np.uint8:
        raise ValueError("expected a uint8 array of shape (height, width, 4)")


def encode_png(pixels: np.ndarray) -> bytes:
    _check(pixels)
    height, width, _ = pixels.shape

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    rows = np.concatenate([np.zeros((height, 1), np.uint8), pixels.reshape(height, width * 4)], axis=1)
    header = struct.pack(">IIBBBBB", width, height, 8, PNG_COLOR_TYPE_RGBA, 0, 0, 0)
    return (
        PNG_SIGNATURE
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows.tobytes(), 9))
        + chunk(b"IEND", b"")
    )


def encode_qoi(pixels: np.ndarray) -> bytes:
    """QOI (https://qoiformat.org), RGBA, sRGB."""
    _check(pixels)
    height, width, _ = pixels.shape
    out = bytearray(QOI_MAGIC + struct.pack(">IIBB", width, height, QOI_CHANNELS_RGBA, QOI_COLORSPACE_SRGB))
    seen = [(0, 0, 0, 0)] * 64
    previous = (0, 0, 0, 255)
    run = 0
    for pixel in map(tuple, pixels.reshape(-1, 4).tolist()):
        if pixel == previous:
            run += 1
            if run == QOI_MAX_RUN:
                out.append(QOI_OP_RUN | (run - 1))
                run = 0
            continue
        if run:
            out.append(QOI_OP_RUN | (run - 1))
            run = 0
        r, g, b, a = pixel
        slot = (r * 3 + g * 5 + b * 7 + a * 11) % 64
        if seen[slot] == pixel:
            out.append(QOI_OP_INDEX | slot)
        else:
            seen[slot] = pixel
            pr, pg, pb, pa = previous
            if a != pa:
                out += bytes((QOI_OP_RGBA, r, g, b, a))
            else:
                dr, dg, db = (r - pr + 2) & 0xFF, (g - pg + 2) & 0xFF, (b - pb + 2) & 0xFF
                vg = (g - pg + 32) & 0xFF
                vg_r = (r - pr - (g - pg) + 8) & 0xFF
                vg_b = (b - pb - (g - pg) + 8) & 0xFF
                if dr < 4 and dg < 4 and db < 4:
                    out.append(QOI_OP_DIFF | (dr << 4) | (dg << 2) | db)
                elif vg < 64 and vg_r < 16 and vg_b < 16:
                    out += bytes((QOI_OP_LUMA | vg, (vg_r << 4) | vg_b))
                else:
                    out += bytes((QOI_OP_RGB, r, g, b))
        previous = pixel
    if run:
        out.append(QOI_OP_RUN | (run - 1))
    return bytes(out) + QOI_END


def decode_qoi(data: bytes) -> np.ndarray:
    """Inverse of encode_qoi (any channel count is read as RGBA); used to check what was written."""
    if data[:4] != QOI_MAGIC:
        raise ValueError("not a QOI image")
    width, height = struct.unpack_from(">II", data, 4)
    seen: list[tuple[int, ...]] = [(0, 0, 0, 0)] * 64
    pixel: tuple[int, ...] = (0, 0, 0, 255)
    pixels: list[tuple[int, ...]] = []
    position = 14
    while len(pixels) < width * height:
        op = data[position]
        position += 1
        if op == QOI_OP_RGB:
            pixel = (*data[position : position + 3], pixel[3])
            position += 3
        elif op == QOI_OP_RGBA:
            pixel = tuple(data[position : position + 4])
            position += 4
        elif op & 0xC0 == QOI_OP_INDEX:
            pixel = seen[op]
        elif op & 0xC0 == QOI_OP_DIFF:
            r, g, b, a = pixel
            pixel = (
                (r + ((op >> 4) & 3) - 2) & 0xFF,
                (g + ((op >> 2) & 3) - 2) & 0xFF,
                (b + (op & 3) - 2) & 0xFF,
                a,
            )
        elif op & 0xC0 == QOI_OP_LUMA:
            r, g, b, a = pixel
            second = data[position]
            position += 1
            dg = (op & 0x3F) - 32
            pixel = (
                (r + dg - 8 + (second >> 4)) & 0xFF,
                (g + dg) & 0xFF,
                (b + dg - 8 + (second & 15)) & 0xFF,
                a,
            )
        else:
            pixels.extend([pixel] * ((op & 0x3F) + 1))
            continue
        seen[(pixel[0] * 3 + pixel[1] * 5 + pixel[2] * 7 + pixel[3] * 11) % 64] = pixel
        pixels.append(pixel)
    return np.array(pixels[: width * height], np.uint8).reshape(height, width, 4)
