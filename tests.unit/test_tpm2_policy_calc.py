# @file tpm2_policy_calc_test.py
# This file contains classes used to calculate TPM 2.0 policies
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import edk2toollib.tpm.tpm2_policy_calc as t2pc


class TestPolicyLocality(unittest.TestCase):
    def test_create_with_empty_list(self):
        policy = t2pc.PolicyLocality(None)
        self.assertEqual(policy.get_bitfield(), 0)
        policy2 = t2pc.PolicyLocality(())
        self.assertEqual(policy2.get_bitfield(), 0)

    def test_create_with_base_localities(self):
        policy = t2pc.PolicyLocality([0, 2, 4])
        self.assertEqual(policy.get_bitfield(), 0b00010101)
        policy2 = t2pc.PolicyLocality([1, 2])
        self.assertEqual(policy2.get_bitfield(), 0b00000110)
        policy3 = t2pc.PolicyLocality([3])
        self.assertEqual(policy3.get_bitfield(), 0b00001000)
        policy4 = t2pc.PolicyLocality([57])
        self.assertEqual(policy4.get_bitfield(), 57)

    def test_create_with_invalid_localites(self):
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([5])
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([12])
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([31])
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([256])

    def test_create_with_mixed_lower_and_upper(self):
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([1, 4, 35])
        with self.assertRaises(ValueError):
            t2pc.PolicyLocality([36, 128])

    def test_get_buffer(self):
        self.assertEqual(t2pc.PolicyLocality([0, 2, 4]).get_buffer_for_digest(), bytearray.fromhex("0000016F" + "15"))
        self.assertEqual(t2pc.PolicyLocality([34]).get_buffer_for_digest(), bytearray.fromhex("0000016F" + "22"))


class TestPolicyCommandCode(unittest.TestCase):
    def test_create_with_no_code(self):
        with self.assertRaises(ValueError):
            t2pc.PolicyCommandCode(None)

    def test_create_with_invalid_code(self):
        with self.assertRaises(ValueError):
            t2pc.PolicyCommandCode("MonkeyValue")
        with self.assertRaises(ValueError):
            t2pc.PolicyCommandCode(12)
        with self.assertRaises(ValueError):
            t2pc.PolicyCommandCode({})

    def test_create_with_valid_codes(self):
        policy = t2pc.PolicyCommandCode("TPM_CC_Clear")
        self.assertEqual(policy.get_code(), "TPM_CC_Clear")
        policy = t2pc.PolicyCommandCode("TPM_CC_ClearControl")
        self.assertEqual(policy.get_code(), "TPM_CC_ClearControl")
        policy = t2pc.PolicyCommandCode("TPM_CC_Quote")
        self.assertEqual(policy.get_code(), "TPM_CC_Quote")

    def test_get_buffer(self):
        self.assertEqual(
            t2pc.PolicyCommandCode("TPM_CC_Clear").get_buffer_for_digest(), bytearray.fromhex("0000016C" + "00000126")
        )
        self.assertEqual(
            t2pc.PolicyCommandCode("TPM_CC_ClearControl").get_buffer_for_digest(),
            bytearray.fromhex("0000016C" + "00000127"),
        )


class TestPolicyTreeSolo(unittest.TestCase):
    def test_policy_command_code(self):
        expected_result_1 = bytearray.fromhex("940CFB4217BB1EDCF7FB41937CA974AA68E698AB78B8124B070113E211FD46FC")
        expected_result_2 = bytearray.fromhex("C4DFABCEDA8DE836C95661952892B1DEF7203AFB46FEFEC43FFCFC93BE540730")
        expected_result_3 = bytearray.fromhex("1D2DC485E177DDD0A40A344913CEEB420CAA093C42587D2E1B132B157CCB5DB0")

        test1 = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_ClearControl"))
        test2 = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_Clear"))
        test3 = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_NV_UndefineSpaceSpecial"))

        policy_hash = t2pc.PolicyHasher("sha256")
        self.assertEqual(test1.get_policy(policy_hash), expected_result_1)
        self.assertEqual(test2.get_policy(policy_hash), expected_result_2)
        self.assertEqual(test3.get_policy(policy_hash), expected_result_3)

    def test_policy_locality(self):
        expected_result = bytearray.fromhex("07039B45BAF2CC169B0D84AF7C53FD1622B033DF0A5DCDA66360AA99E54947CD")

        test = t2pc.PolicyTreeSolo(t2pc.PolicyLocality([3, 4]))

        policy_hash = t2pc.PolicyHasher("sha256")
        self.assertEqual(test.get_policy(policy_hash), expected_result)


class TestPolicyTreeAnd(unittest.TestCase):
    def test_single_and_should_match_solo(self):
        soloTest = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_Clear"))
        andTest = t2pc.PolicyTreeAnd([t2pc.PolicyCommandCode("TPM_CC_Clear")])

        policy_hash = t2pc.PolicyHasher("sha256")
        self.assertEqual(soloTest.get_policy(policy_hash), andTest.get_policy(policy_hash))


class TestPolicyTreeOr(unittest.TestCase):
    def test_single_and_should_match_solo(self):
        expected_result = bytearray.fromhex("3F44FB41486D4A36A8ADCA2203E73A5068BFED5FDCE5092B9A3C6CCE8ABF3B0C")

        test1 = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_ClearControl"))
        test2 = t2pc.PolicyTreeSolo(t2pc.PolicyCommandCode("TPM_CC_Clear"))
        orTest = t2pc.PolicyTreeOr([test1, test2])

        policy_hash = t2pc.PolicyHasher("sha256")
        self.assertEqual(orTest.get_policy(policy_hash), expected_result)


class TestPolicyTree(unittest.TestCase):
    def test_complex_policy_1(self):
        expected_result = bytearray.fromhex("DFFDB6C8EAFCBE691E358882B18703121EAB40DE2386F7A8E7B4A06591E1F0EE")

        # Computation details:
        #   A = TPM2_PolicyLocality(3 & 4)
        #   B = TPM2_PolicyCommandCode(TPM_CC_NV_UndefineSpaceSpecial)
        #   C = TPM2_PolicyCommandCode(TPM_CC_NV_Write)
        #   policy = {{A} AND {C}} OR {{A} AND {B}}

        a = t2pc.PolicyLocality([3, 4])
        b = t2pc.PolicyCommandCode("TPM_CC_NV_UndefineSpaceSpecial")
        c = t2pc.PolicyCommandCode("TPM_CC_NV_Write")

        leg1 = t2pc.PolicyTreeAnd([a, c])
        leg2 = t2pc.PolicyTreeAnd([a, b])
        final = t2pc.PolicyTreeOr([leg1, leg2])

        policy_hash = t2pc.PolicyHasher("sha256")
        self.assertEqual(final.get_policy(policy_hash), expected_result)


if __name__ == "__main__":
    unittest.main()
