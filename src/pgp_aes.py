"""PGP-AES : message chiffré avec AES-128, clé chiffrée avec RSA."""

import re

import aes
import rsa


def parse_key(key):
    """Lit clé AES (ou clé chiffrée RSA) : exposant-module."""
    parts = key.split(":")
    if len(parts) != 2:
        raise ValueError("PGP-AES key must have the format symmetric-key:exponent-modulus")
    symmetric, asymmetric = parts
    if not symmetric or len(symmetric) % 2 or re.fullmatch(r"[0-9a-fA-F]+", symmetric) is None:
        raise ValueError("expected a non-empty hexadecimal value with complete bytes")
    rsa.parse_key(asymmetric)
    return bytes.fromhex(symmetric), asymmetric


# Chiffrement

def encrypt(data, key, block_mode=False):
    """Renvoie (clé AES chiffrée par RSA, message chiffré par AES)."""
    symmetric, asymmetric = parse_key(key)
    if len(symmetric) != aes.BLOCK_SIZE:
        raise ValueError("PGP-AES requires a 16-byte AES key")
    encrypted_key = rsa.encrypt(symmetric, asymmetric)
    return encrypted_key, aes.encrypt(data, symmetric, block_mode)


# Déchiffrement

def decrypt(data, key, block_mode=False):
    """Récupère les 16 octets de clé AES avec RSA, puis déchiffre le message."""
    encrypted_key, asymmetric = parse_key(key)
    symmetric = rsa.decrypt(encrypted_key, asymmetric)
    if len(symmetric) > aes.BLOCK_SIZE:
        raise ValueError("decrypted AES key exceeds 16 bytes")
    # RSA renvoie une représentation minimale : restaurer les zéros terminaux.
    symmetric = symmetric.ljust(aes.BLOCK_SIZE, b"\x00")
    return aes.decrypt(data, symmetric, block_mode)
