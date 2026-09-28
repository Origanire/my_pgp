"""PGP-XOR : message chiffré avec XOR et clé symétrique chiffrée avec RSA."""

import re

import rsa
import xor


def parse_key(key):
    """Lit une clé symétrique hexadécimale suivie de la clé RSA."""
    parts = key.split(":")
    if len(parts) != 2:
        raise ValueError("PGP-XOR key must have the format symmetric-key:exponent-modulus")
    symmetric, asymmetric = parts
    if not symmetric or len(symmetric) % 2 or re.fullmatch(r"[0-9a-fA-F]+", symmetric) is None:
        raise ValueError("expected a non-empty hexadecimal value with complete bytes")
    rsa.parse_key(asymmetric)
    return bytes.fromhex(symmetric), asymmetric


# Chiffrement

def encrypt(data, key, block_mode=False):
    """Renvoie le couple (clé chiffrée par RSA, message chiffré par XOR)."""
    symmetric, asymmetric = parse_key(key)
    encrypted_key = rsa.encrypt(symmetric, asymmetric)
    return encrypted_key, xor.encrypt(data, symmetric, block_mode)


# Déchiffrement

def decrypt(data, key, block_mode=False):
    """Récupère la clé XOR avec RSA, puis déchiffre le message."""
    encrypted_key, asymmetric = parse_key(key)
    symmetric = rsa.decrypt(encrypted_key, asymmetric)
    # En bloc, la taille du message permet de restituer les zéros de la clé.
    if block_mode:
        symmetric = symmetric.ljust(len(data), b"\x00")
    return xor.decrypt(data, symmetric, block_mode)
