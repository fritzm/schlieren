"""Prusa binary G-code (.bgcode) container: read the blocks, check them, and replace the thumbnails.

Layout (libbgcode, version 1; confirmed against PrusaSlicer-sliced files):

    file header   magic "GCDE", version u32, checksum type u16 (0 none, 1 CRC32)        10 bytes
    block         type u16, compression u16, uncompressed size u32,
                  [compressed size u32 if compression != 0], parameters, data, [CRC32 u32]
                  the CRC32 covers the header, parameters and data
    block order   file metadata, printer metadata, thumbnails, print metadata, slicer metadata, G-code

Thumbnail blocks are never compressed; their parameters are format u16 (PNG, JPG, QOI), width u16 and
height u16. Only that is needed to swap thumbnails, so every other block is carried as opaque bytes and the
G-code blocks are never decoded or rewritten.
"""

import struct
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum

from schlieren.gcode_codecs import heatshrink_decode, meatpack_decode

MAGIC = b"GCDE"
VERSION = 1
FILE_HEADER = struct.Struct("<4sIH")
BLOCK_HEADER = struct.Struct("<HHI")
COMPRESSED_SIZE = struct.Struct("<I")
THUMBNAIL_PARAMETERS = struct.Struct("<HHH")
CRC = struct.Struct("<I")
CHECKSUM_NONE, CHECKSUM_CRC32 = 0, 1


class BlockType(IntEnum):
    FILE_METADATA = 0
    GCODE = 1
    SLICER_METADATA = 2
    PRINTER_METADATA = 3
    PRINT_METADATA = 4
    THUMBNAIL = 5


class ImageFormat(IntEnum):
    PNG = 0
    JPG = 1
    QOI = 2


class Compression(IntEnum):
    NONE = 0
    DEFLATE = 1
    HEATSHRINK_11_4 = 2
    HEATSHRINK_12_4 = 3


METADATA_BLOCKS = (
    BlockType.FILE_METADATA,
    BlockType.PRINTER_METADATA,
    BlockType.PRINT_METADATA,
    BlockType.SLICER_METADATA,
)
GCODE_ENCODING_MEATPACK = (1, 2)  # MeatPack, and MeatPack with comments.


class BgcodeError(ValueError):
    pass


@dataclass(frozen=True)
class Block:
    type: int
    raw: bytes  # The whole block as stored, checksum included.
    parameters: bytes  # The block's parameters (encoding, or a thumbnail's format and size).
    data: bytes  # The stored data (compressed, if the block is).

    @property
    def compression(self) -> Compression:
        return Compression(BLOCK_HEADER.unpack_from(self.raw)[1])

    @property
    def uncompressed_size(self) -> int:
        return BLOCK_HEADER.unpack_from(self.raw)[2]

    def payload(self) -> bytes:
        """The block's data, decompressed (a G-code block's is still MeatPack-encoded)."""
        match self.compression:
            case Compression.NONE:
                return self.data
            case Compression.DEFLATE:
                return zlib.decompress(self.data)
            case Compression.HEATSHRINK_11_4:
                return heatshrink_decode(self.data, self.uncompressed_size, 11, 4)
            case Compression.HEATSHRINK_12_4:
                return heatshrink_decode(self.data, self.uncompressed_size, 12, 4)

    @property
    def thumbnail(self) -> tuple[ImageFormat, int, int] | None:
        """(format, width, height) of a thumbnail block, else None."""
        if self.type != BlockType.THUMBNAIL:
            return None
        image_format, width, height = THUMBNAIL_PARAMETERS.unpack(self.parameters)
        return ImageFormat(image_format), width, height


@dataclass(frozen=True)
class Bgcode:
    header: bytes
    blocks: tuple[Block, ...]

    @property
    def checksum_type(self) -> int:
        return FILE_HEADER.unpack(self.header)[2]

    def to_bytes(self) -> bytes:
        return self.header + b"".join(block.raw for block in self.blocks)

    def metadata(self, kind: BlockType) -> dict[str, str]:
        """The key=value lines of a metadata block (file, printer, print or slicer); {} if the file has none."""
        if kind not in METADATA_BLOCKS:
            raise ValueError(f"{kind.name} is not a metadata block")
        found: dict[str, str] = {}
        for block in self.blocks:
            if block.type == kind:
                for line in block.payload().decode("utf-8").splitlines():
                    key, separator, value = line.partition("=")
                    if separator:
                        found[key.strip()] = value.strip()
        return found

    def gcode(self) -> str:
        """The whole G-code as text (MeatPack's newlines leave blank lines between commands)."""
        parts = []
        for block in self.blocks:
            if block.type == BlockType.GCODE:
                (encoding,) = struct.unpack("<H", block.parameters)
                if encoding not in (0, *GCODE_ENCODING_MEATPACK):
                    raise BgcodeError(f"unknown G-code encoding {encoding}")
                payload = block.payload()
                parts.append(meatpack_decode(payload) if encoding else payload.decode("utf-8"))
        return "".join(parts)


def parse(data: bytes) -> Bgcode:
    """Split a .bgcode into its blocks, verifying the header and every block checksum."""
    if len(data) < FILE_HEADER.size:
        raise BgcodeError("file shorter than the bgcode header")
    magic, version, checksum_type = FILE_HEADER.unpack_from(data)
    if magic != MAGIC:
        raise BgcodeError(f"not a bgcode file (magic {magic!r})")
    if version != VERSION:
        raise BgcodeError(f"unsupported bgcode version {version}")
    if checksum_type not in (CHECKSUM_NONE, CHECKSUM_CRC32):
        raise BgcodeError(f"unknown checksum type {checksum_type}")
    checksum_size = CRC.size if checksum_type == CHECKSUM_CRC32 else 0

    blocks = []
    position = FILE_HEADER.size
    while position < len(data):
        start = position
        if start + BLOCK_HEADER.size > len(data):
            raise BgcodeError(f"truncated block header at byte {start}")
        block_type, compression, size = BLOCK_HEADER.unpack_from(data, position)
        position += BLOCK_HEADER.size
        if compression:
            (size,) = COMPRESSED_SIZE.unpack_from(data, position)
            position += COMPRESSED_SIZE.size
        try:
            kind = BlockType(block_type)
        except ValueError:
            raise BgcodeError(f"unknown block type {block_type} at byte {start}") from None
        parameter_size = THUMBNAIL_PARAMETERS.size if kind == BlockType.THUMBNAIL else 2
        end = position + parameter_size + size + checksum_size
        if end > len(data):
            raise BgcodeError(f"block at byte {start} runs past the end of the file")
        if (
            checksum_size
            and zlib.crc32(data[start : end - checksum_size])
            != (CRC.unpack_from(data, end - checksum_size)[0])
        ):
            raise BgcodeError(f"checksum mismatch in block at byte {start}")
        blocks.append(
            Block(
                block_type,
                data[start:end],
                data[position : position + parameter_size],
                data[position + parameter_size : end - checksum_size],
            )
        )
        position = end
    return Bgcode(data[: FILE_HEADER.size], tuple(blocks))


def thumbnail_block(
    image_format: ImageFormat, width: int, height: int, image: bytes, checksum_type: int = CHECKSUM_CRC32
) -> Block:
    """A thumbnail block holding the already-encoded image."""
    parameters = THUMBNAIL_PARAMETERS.pack(image_format, width, height)
    body = BLOCK_HEADER.pack(BlockType.THUMBNAIL, 0, len(image)) + parameters + image
    raw = body + CRC.pack(zlib.crc32(body)) if checksum_type == CHECKSUM_CRC32 else body
    return Block(BlockType.THUMBNAIL, raw, parameters, image)


def replace_thumbnails(file: Bgcode, thumbnails: Iterable[Block]) -> Bgcode:
    """file with its thumbnail blocks (if any) replaced by thumbnails, placed after the printer metadata."""
    kept = [block for block in file.blocks if block.type != BlockType.THUMBNAIL]
    after = [i for i, block in enumerate(kept) if block.type == BlockType.PRINTER_METADATA]
    if not after:
        raise BgcodeError("no printer-metadata block to place the thumbnails after")
    index = after[-1] + 1
    return Bgcode(file.header, (*kept[:index], *thumbnails, *kept[index:]))
