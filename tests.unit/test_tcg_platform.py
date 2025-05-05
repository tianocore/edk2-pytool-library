import unittest

from edk2toollib.tpm.tcg_platform import (
    TpmtHa,
    SHA1_DIGEST_SIZE,
    SHA256_DIGEST_SIZE,
    SHA384_DIGEST_SIZE,
    SHA512_DIGEST_SIZE,
    TPM_ALG_SHA1,
    TPM_ALG_SHA256,
    TPM_ALG_SHA384,
    TPM_ALG_SHA512
)

class TpmtHa_Test(unittest.TestCase):
    def test_initialize_by_digest(self):
        test = TpmtHa(b"\x00" * SHA384_DIGEST_SIZE)
        self.assertEqual(test.HashAlg, TPM_ALG_SHA384)
        test = TpmtHa(b"\x00" * SHA512_DIGEST_SIZE)
        self.assertEqual(test.HashAlg, TPM_ALG_SHA512)

        with self.assertRaises(ValueError):
            test = TpmtHa(b"\x00" * 13)

    def test_initialize_by_alg(self):
        test = TpmtHa(alg=TPM_ALG_SHA384)
        self.assertEqual(len(test.HashDigest), SHA384_DIGEST_SIZE)
        test = TpmtHa(digest=None, alg=TPM_ALG_SHA256)
        self.assertEqual(len(test.HashDigest), SHA256_DIGEST_SIZE)
        test = TpmtHa(digest=None, alg=TPM_ALG_SHA1)
        self.assertEqual(len(test.HashDigest), SHA1_DIGEST_SIZE)

        with self.assertRaises(ValueError):
            test = TpmtHa(alg=0x00)
        with self.assertRaises(ValueError):
            test = TpmtHa(alg=0xFF)

    def test_reset_with_locality(self):
        test = TpmtHa()
        self.assertEqual(test.HashAlg, TPM_ALG_SHA256)
        self.assertEqual(test.HashDigest, b"\x00" * SHA256_DIGEST_SIZE)
        test.reset_with_locality(3)
        self.assertEqual(
            test.HashDigest, (b"\x00" * (SHA256_DIGEST_SIZE - 1)) + b"\x03"
        )
        test.reset_with_locality(2)
        self.assertEqual(
            test.HashDigest, (b"\x00" * (SHA256_DIGEST_SIZE - 1)) + b"\x02"
        )

        test = TpmtHa(alg=TPM_ALG_SHA384).reset_with_locality(4)
        self.assertEqual(
            test.HashDigest, (b"\x00" * (SHA384_DIGEST_SIZE - 1)) + b"\x04"
        )

        with self.assertRaises(ValueError):
            test = TpmtHa()
            test.reset_with_locality(5)
        with self.assertRaises(ValueError):
            test = TpmtHa()
            test.reset_with_locality(-1)