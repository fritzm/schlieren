"""Decoders for the G-code encodings inside a bgcode: heatshrink (compression) and MeatPack (text packing).

PrusaSlicer writes the G-code blocks heatshrink-compressed (window 2^12, lookahead 2^4, window starting
zeroed) and MeatPack-encoded with comments kept.
"""

HEATSHRINK_WINDOW_BITS = 12
HEATSHRINK_LOOKAHEAD_BITS = 4

# MeatPack: a pair of characters per byte, low nibble first; nibble 15 means that character follows as a full
# byte. Two 0xFF bytes introduce a command byte.
MEATPACK_ALPHABET = "0123456789. \nGX"
MEATPACK_FULL_BYTE = 15
MEATPACK_SIGNAL = 0xFF
MEATPACK_NO_SPACES_CHAR = "E"  # Nibble 11 is a space, or this with no-spaces on.
MEATPACK_SPACE_NIBBLE = 11
MEATPACK_COMMANDS = {
    246: "disable no-spaces",
    247: "enable no-spaces",
    249: "reset",
    250: "disable packing",
    251: "enable packing",
    253: "toggle packing",
}


def heatshrink_decode(
    data: bytes,
    size: int,
    window_bits: int = HEATSHRINK_WINDOW_BITS,
    lookahead_bits: int = HEATSHRINK_LOOKAHEAD_BITS,
) -> bytes:
    """Decompress a heatshrink stream to `size` bytes.

    The stream is bits, most significant first: a 1 tag then a literal byte, or a 0 tag then a back-reference
    (offset - 1, window_bits; length - 1, lookahead_bits). Offsets reaching before the start read zeros.
    """
    out = bytearray()
    position = 0
    total_bits = len(data) * 8

    def read(count: int) -> int:
        nonlocal position
        if position + count > total_bits:
            raise EOFError
        value = 0
        for _ in range(count):
            value = (value << 1) | ((data[position >> 3] >> (7 - (position & 7))) & 1)
            position += 1
        return value

    try:
        while len(out) < size:
            if read(1):
                out.append(read(8))
            else:
                offset = read(window_bits) + 1
                for _ in range(read(lookahead_bits) + 1):
                    out.append(out[-offset] if len(out) >= offset else 0)
    except EOFError:
        pass  # The last byte is padded with zero bits, which read as a truncated tag.
    if len(out) < size:
        raise ValueError(f"heatshrink stream ended after {len(out)} of {size} bytes")
    return bytes(out[:size])


def meatpack_decode(data: bytes) -> str:
    """The text of a MeatPack stream (packing starts off; the stream's commands switch it)."""
    out: list[str] = []
    packing = no_spaces = False
    i = 0
    while i < len(data):
        byte = data[i]
        if byte == MEATPACK_SIGNAL and data[i + 1 : i + 2] == bytes([MEATPACK_SIGNAL]) and i + 2 < len(data):
            command = data[i + 2]
            i += 3
            if command not in MEATPACK_COMMANDS:
                raise ValueError(f"unknown MeatPack command {command}")
            if command == 251:
                packing = True
            elif command == 250:
                packing = False
            elif command == 253:
                packing = not packing
            elif command == 247:
                no_spaces = True
            elif command == 246:
                no_spaces = False
            else:  # 249: reset
                packing = no_spaces = False
            continue
        i += 1
        if not packing:
            out.append(chr(byte))
            continue
        pair = []
        for nibble in (byte & 15, byte >> 4):
            if nibble == MEATPACK_FULL_BYTE:
                if i >= len(data):
                    raise ValueError("MeatPack stream ends inside a full-byte character")
                pair.append(chr(data[i]))
                i += 1
            elif nibble == MEATPACK_SPACE_NIBBLE and no_spaces:
                pair.append(MEATPACK_NO_SPACES_CHAR)
            else:
                pair.append(MEATPACK_ALPHABET[nibble])
        out.extend(pair)
    return "".join(out)
