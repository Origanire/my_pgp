#!/usr/bin/env python3
"""Première étape de my_pgp : interface et chiffrement XOR."""

import re
import sys


HELP = """USAGE
    ./my_pgp CRYPTO_SYSTEM MODE [OPTIONS] [key]

DESCRIPTION
    Cipher or decipher MESSAGE read from standard input.

    CRYPTO_SYSTEM
        xor         XOR algorithm (implemented)
        aes         AES algorithm (not implemented yet)
        rsa         RSA algorithm (not implemented yet)
        pgp-xor     RSA and XOR (not implemented yet)
        pgp-aes     RSA and AES (not implemented yet)

    MODE
        -c          Cipher a clear message
        -d          Decipher a hexadecimal message
        -g P Q      Generate RSA keys (not implemented yet)

    OPTIONS
        -b          Process one block, the same size as the key

    key             Non-empty hexadecimal key in little-endian order
"""


def parse_hex(value):
    """Un octet est représenté par exactement deux chiffres hexadécimaux."""
    if not value or len(value) % 2 or re.fullmatch(r"[0-9a-fA-F]+", value) is None:
        raise ValueError("expected a non-empty hexadecimal value with complete bytes")
    return bytes.fromhex(value)


def parse_arguments(arguments):
    if len(arguments) < 3:
        raise ValueError("expected CRYPTO_SYSTEM MODE [-b] key; use -h for help")
    system, mode, *remaining = arguments
    if system not in ("xor", "aes", "rsa", "pgp-xor", "pgp-aes"):
        raise ValueError("unknown cryptosystem: " + system)
    if system != "xor":
        raise ValueError(system + " is not implemented yet")
    if mode not in ("-c", "-d"):
        raise ValueError("XOR mode must be -c or -d")
    block_mode = remaining[0] == "-b"
    if block_mode:
        remaining = remaining[1:]
    if len(remaining) != 1:
        raise ValueError("expected exactly one key after the optional -b flag")
    return mode, block_mode, parse_hex(remaining[0])


def xor_message(data, key, decrypt=False, block_mode=False):
    """Traite chaque bloc selon la représentation little-endian du sujet."""
    size = len(key)
    if block_mode and len(data) != size:
        raise ValueError("in block mode, the message and key must have the same size")
    if decrypt and len(data) % size:
        raise ValueError("ciphertext must contain complete blocks")
    result = bytearray()
    for offset in range(0, len(data), size):
        block = data[offset:offset + size]
        if decrypt:
            clear = bytes(byte ^ mask for byte, mask in zip(block, key))
            result.extend(clear[::-1])
        else:
            # Compléter le dernier bloc avant de le convertir en nombre.
            block = block.ljust(size, b"\x00")
            result.extend(byte ^ mask for byte, mask in zip(block[::-1], key))
    return bytes(result)


def main():
    if sys.argv[1:] == ["-h"]:
        print(HELP, end="")
        return 0
    try:
        mode, block_mode, key = parse_arguments(sys.argv[1:])
        data = sys.stdin.buffer.read()
        # Le LF terminal est ignoré en bloc et dans la représentation hex.
        if (block_mode or mode == "-d") and data.endswith(b"\n"):
            data = data[:-1]
        if block_mode and b"\n" in data:
            raise ValueError("block mode expects a single line")
        if mode == "-d":
            data = parse_hex(data.decode("ascii")) if data else b""
        result = xor_message(data, key, mode == "-d", block_mode)
        if mode == "-c":
            sys.stdout.buffer.write(result.hex().encode("ascii") + b"\n")
        else:
            sys.stdout.buffer.write(result + (b"\n" if block_mode else b""))
        return 0
    except (ValueError, OSError) as error:
        print("my_pgp: " + str(error), file=sys.stderr)
        return 84


if __name__ == "__main__":
    sys.exit(main())
