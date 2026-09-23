"""AES : vecteurs FIPS 197, exemple du sujet et interface complète."""
import unittest

from src import aes
from test_cli import run


KEY = "57696e74657220697320636f6d696e67"
CLEAR = b"All men must die\n"
CIPHER = b"744ce22c385958348f0df26eceb62eef\n"


class AesTests(unittest.TestCase):
    def test_standard_vectors(self):
        # FIPS 197, annexe C.1, puis vecteur AES-128 entièrement nul.
        vectors = [
            ("000102030405060708090a0b0c0d0e0f",
             "00112233445566778899aabbccddeeff",
             "69c4e0d86a7b0430d8cdb78070b4c55a"),
            ("00" * 16, "00" * 16, "66e94bd4ef8a2c3b884cfa59ca342b2e"),
        ]
        for key, clear, cipher in vectors:
            with self.subTest(key=key):
                rounds = aes._expand_key(bytes.fromhex(key))
                self.assertEqual(aes._encrypt_block(bytes.fromhex(clear), rounds),
                                 bytes.fromhex(cipher))
                self.assertEqual(aes._decrypt_block(bytes.fromhex(cipher), rounds),
                                 bytes.fromhex(clear))

    def test_subject_encryption(self):
        result = run("aes", "-c", "-b", KEY, data=CLEAR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, CIPHER)

    def test_subject_decryption(self):
        result = run("aes", "-d", "-b", KEY, data=CIPHER)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, CLEAR)

    def test_block_without_newline(self):
        result = run("aes", "-c", "-b", KEY, data=CLEAR[:-1])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, CIPHER)

    def test_stream_roundtrip(self):
        for data in (b"", b"A", b"A" * 15, b"A" * 16, b"A" * 17,
                     bytes(range(256)), b"first line\nsecond line\n\x00"):
            with self.subTest(length=len(data)):
                cipher = run("aes", "-c", KEY, data=data)
                self.assertEqual(cipher.returncode, 0, cipher.stderr)
                self.assertEqual(len(cipher.stdout), ((len(data) + 15) // 16) * 32 + 1)
                clear = run("aes", "-d", KEY, data=cipher.stdout)
                self.assertEqual(clear.returncode, 0, clear.stderr)
                self.assertEqual(clear.stdout, data + b"\x00" * (-len(data) % 16))

    def test_stream_full_blocks_match_subject(self):
        result = run("aes", "-c", KEY, data=CLEAR[:-1] * 2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, CIPHER[:-1] * 2 + b"\n")

    def test_invalid_inputs(self):
        cases = [
            (["-c", "00" * size], b"A" * 16)
            for size in (1, 15, 17, 24, 32)
        ]
        cases += [(["-c", "-b", KEY], b"A" * size) for size in (0, 15, 17, 32)]
        cases += [(["-d", KEY], b"00" * 15),
                  (["-d", "-b", KEY], b""),
                  (["-d", "-b", KEY], b"00" * 32),
                  (["-d", KEY], b"not hexadecimal")]
        for args, data in cases:
            with self.subTest(args=args, length=len(data)):
                result = run("aes", *args, data=data)
                self.assertEqual(result.returncode, 84)
                self.assertEqual(result.stdout, b"")
                self.assertTrue(result.stderr)


if __name__ == "__main__":
    unittest.main()
