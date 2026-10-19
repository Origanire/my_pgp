"""Tests PGP-AES à travers la véritable interface CLI."""
import unittest

from test_cli import run
from test_rsa import N, D


class PgpAesTests(unittest.TestCase):
    def test_composition_with_rsa_and_aes(self):
        key = '57696e74657220697320636f6d696e67'
        data = b'All men must die\n'
        result = run('pgp-aes', '-c', '-b', key + ':010001-' + N, data=data)
        rsa_result = run('rsa', '-c', '010001-' + N, data=bytes.fromhex(key))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, rsa_result.stdout + b'744ce22c385958348f0df26eceb62eef\n')
        encrypted_key, message = result.stdout.split(b'\n', 1)
        clear = run('pgp-aes', '-d', '-b', encrypted_key.decode() + ':' + D + '-' + N,
                    data=message)
        self.assertEqual(clear.returncode, 0, clear.stderr)
        self.assertEqual(clear.stdout, data)

    def test_roundtrips_and_key_zero_restoration(self):
        for key in ('00' * 16, '01' + '00' * 15, 'ab' * 16):
            for block, data in ((True, b'0123456789abcdef\n'),
                                (False, b'ABC'), (False, bytes(range(256)) + b'\n'),
                                (False, b'')):
                with self.subTest(key=key, block=block, data=data):
                    flags = ['-b'] if block else []
                    cipher = run('pgp-aes', '-c', *flags, key + ':010001-' + N, data=data)
                    self.assertEqual(cipher.returncode, 0, cipher.stderr)
                    encrypted_key, message = cipher.stdout.split(b'\n', 1)
                    clear = run('pgp-aes', '-d', *flags,
                                encrypted_key.decode() + ':' + D + '-' + N, data=message)
                    expected = data if block else data + b'\x00' * (-len(data) % 16)
                    self.assertEqual(clear.returncode, 0, clear.stderr)
                    self.assertEqual(clear.stdout, expected)

    def test_invalid_inputs(self):
        public = '010001-' + N
        private = D + '-' + N
        oversized = run('rsa', '-c', public, data=b'A' * 17).stdout.strip().decode()
        self.assertTrue(oversized)
        for mode, flags, key, data in [
            ('-c', [], '01', b'A'),
            ('-c', [], ':' + public, b'A'),
            ('-c', [], 'zz:' + public, b'A'),
            ('-c', [], '0:' + public, b'A'),
            ('-c', [], '01:' + public + ':01', b'A'),
            ('-c', [], '01:' + public, b'A'),
            ('-c', [], 'aa' * 17 + ':' + public, b'A'),
            ('-c', [], 'aa' * 16 + ':0101-19bb', b'A'),
            ('-c', ['-b'], 'aa' * 16 + ':' + public, b'A'),
            ('-d', [], N + ':' + private, b''),
            ('-d', [], oversized + ':' + private, b''),
            ('-d', [], '00:' + private, b'00'),
            ('-d', [], '00:' + private, b'zz'),
        ]:
            with self.subTest(mode=mode, key=key, data=data):
                result = run('pgp-aes', mode, *flags, key, data=data)
                self.assertEqual(result.returncode, 84)
                self.assertEqual(result.stdout, b'')
                self.assertTrue(result.stderr)
