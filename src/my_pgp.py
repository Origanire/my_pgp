#!/usr/bin/env python3
"""Première étape de my_pgp : interface et chiffrements XOR / AES-128."""

import re
import sys

import aes
import pgp_aes
import pgp_xor
import rsa
import xor


SYSTEMS = {
    "xor": xor,
    "aes": aes,
    "rsa": rsa,
    "pgp-xor": pgp_xor,
    "pgp-aes": pgp_aes,
}


HELP = """USAGE
    ./my_pgp CRYPTO_SYSTEM MODE [OPTIONS] [key]

DESCRIPTION
    Cipher or decipher MESSAGE read from standard input.

    CRYPTO_SYSTEM
        xor         XOR algorithm (implemented)
        aes         AES-128 algorithm (implemented)
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
    if system not in SYSTEMS:
        raise ValueError("unknown cryptosystem: " + system)
    if system not in ("xor", "aes"):
        raise ValueError(system + " is not implemented yet")
    if mode not in ("-c", "-d"):
        raise ValueError(system.upper() + " mode must be -c or -d")
    block_mode = remaining[0] == "-b"
    if block_mode:
        remaining = remaining[1:]
    if len(remaining) != 1:
        raise ValueError("expected exactly one key after the optional -b flag")
    return SYSTEMS[system], mode, block_mode, parse_hex(remaining[0])



def main():
    if sys.argv[1:] == ["-h"]:
        print(HELP, end="")
        return 0
    try:
        system, mode, block_mode, key = parse_arguments(sys.argv[1:])
        data = sys.stdin.buffer.read()
        # Le LF terminal est ignoré en bloc et dans la représentation hex.
        if (block_mode or mode == "-d") and data.endswith(b"\n"):
            data = data[:-1]
        if block_mode and b"\n" in data:
            raise ValueError("block mode expects a single line")
        if mode == "-d":
            data = parse_hex(data.decode("ascii")) if data else b""
        operation = system.encrypt if mode == "-c" else system.decrypt
        result = operation(data, key, block_mode)
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
