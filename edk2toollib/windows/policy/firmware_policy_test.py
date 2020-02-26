# @file
# UnitTest for firmware_policy.py
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
import secrets
import io
from edk2toollib.windows.policy.firmware_policy import FirmwarePolicy, Reserved2, PolicyValueType


class FirmwarePolicyTest(unittest.TestCase):

    # A server-generated, non-firmware policy with 1 rule
    #   Key: 81000000_Debug_DeviceID
    #   ValueType: 5
    #   Value:  0xc2e28c3a948caef6
    TEST_DEVICEID_C2E28 = bytearray.fromhex(
        """
        02 00 01 00 00 00 2E D8 DA 0C 39 D8 54 47 89 A1
        84 4A B2 82 31 2B 00 00 10 02 00 00 00 00 01 00
        00 00 00 81 00 00 00 00 0C 00 00 00 1E 00 00 00
        0A 00 44 00 65 00 62 00 75 00 67 00 10 00 44 00
        65 00 76 00 69 00 63 00 65 00 49 00 44 00 05 00
        F6 AE 8C 94 3A 8C E2 C2""")

    TEST_LEGACY_POLICY = bytearray.fromhex(
        """
        02 00 01 00 00 00 9B 42 B2 25 93 6E FB 4D 9B DF
        28 62 43 B2 19 70 00 00 AC AD 00 00 11 00 38 00
        00 00 00 00 49 00 00 16 00 00 00 00 00 00 00 00
        10 00 00 16 04 00 00 00 00 00 00 00 48 00 00 16
        08 00 00 00 00 00 00 00 40 00 00 16 0C 00 00 00
        00 00 00 00 41 00 00 16 10 00 00 00 00 00 00 00
        60 00 00 16 14 00 00 00 03 00 20 10 43 00 00 11
        18 00 00 00 04 00 20 10 43 00 00 11 1C 00 00 00
        03 00 20 10 53 00 00 22 20 00 00 00 03 00 20 10
        F2 00 00 26 24 00 00 00 03 00 20 10 A0 00 00 26
        28 00 00 00 03 00 20 10 25 00 00 26 2C 00 00 00
        03 00 20 10 20 00 00 25 30 00 00 00 03 00 20 10
        81 00 00 26 3A 00 00 00 04 00 20 10 06 00 00 26
        3E 00 00 00 04 00 20 10 01 00 00 21 42 00 00 00
        06 00 30 10 01 00 00 22 46 00 00 00 00 00 00 81
        4A 00 00 00 5C 00 00 00 72 00 00 00 00 00 00 81
        4A 00 00 00 8E 00 00 00 B6 00 00 00 00 00 00 81
        C0 00 00 00 DC 00 00 00 E8 00 00 00 00 00 00 81
        EE 00 00 00 0E 01 00 00 2E 01 00 00 00 00 00 81
        80 01 00 00 0E 01 00 00 A0 01 00 00 00 00 00 81
        F2 01 00 00 0E 01 00 00 12 02 00 00 00 00 00 81
        64 02 00 00 DC 00 00 00 8A 02 00 00 00 00 00 81
        90 02 00 00 0E 01 00 00 BA 02 00 00 00 00 00 81
        0C 03 00 00 0E 01 00 00 36 03 00 00 00 00 00 81
        88 03 00 00 DC 00 00 00 9E 03 00 00 00 00 00 81
        A4 03 00 00 BE 03 00 00 D2 03 00 00 00 00 00 81
        A4 03 00 00 D8 03 00 00 E2 03 00 00 00 00 00 81
        F2 03 00 00 BE 03 00 00 0C 04 00 00 00 00 00 81
        12 04 00 00 BE 03 00 00 2C 04 00 00 00 00 00 81
        12 04 00 00 D8 03 00 00 32 04 00 00 00 00 00 81
        42 04 00 00 BE 03 00 00 5C 04 00 00 00 00 00 81
        42 04 00 00 D8 03 00 00 62 04 00 00 00 00 00 81
        88 04 00 00 BE 03 00 00 A2 04 00 00 00 00 00 81
        88 04 00 00 D8 03 00 00 A8 04 00 00 00 00 00 81
        CE 04 00 00 BE 03 00 00 E8 04 00 00 00 00 00 81
        CE 04 00 00 D8 03 00 00 EE 04 00 00 00 00 00 81
        FE 04 00 00 BE 03 00 00 18 05 00 00 00 00 00 81
        FE 04 00 00 D8 03 00 00 1E 05 00 00 00 00 00 81
        2E 05 00 00 BE 03 00 00 48 05 00 00 00 00 00 81
        2E 05 00 00 D8 03 00 00 4E 05 00 00 00 00 00 81
        5E 05 00 00 BE 03 00 00 78 05 00 00 00 00 00 81
        5E 05 00 00 D8 03 00 00 7E 05 00 00 00 00 00 81
        8E 05 00 00 BE 03 00 00 A8 05 00 00 00 00 00 81
        8E 05 00 00 D8 03 00 00 AE 05 00 00 00 00 00 81
        BE 05 00 00 BE 03 00 00 DA 05 00 00 00 00 00 81
        BE 05 00 00 D8 03 00 00 E0 05 00 00 00 00 00 81
        F0 05 00 00 BE 03 00 00 0C 06 00 00 00 00 00 81
        F0 05 00 00 D8 03 00 00 12 06 00 00 00 00 00 81
        22 06 00 00 BE 03 00 00 3E 06 00 00 00 00 00 81
        22 06 00 00 D8 03 00 00 44 06 00 00 00 00 00 81
        54 06 00 00 BE 03 00 00 70 06 00 00 00 00 00 81
        76 06 00 00 BE 03 00 00 92 06 00 00 00 00 00 81
        98 06 00 00 BE 03 00 00 B4 06 00 00 00 00 00 81
        BA 06 00 00 BE 03 00 00 D6 06 00 00 00 00 00 81
        BA 06 00 00 D8 03 00 00 DC 06 00 00 00 00 00 81
        EC 06 00 00 0A 07 00 00 2E 07 00 00 00 00 00 81
        42 07 00 00 60 07 00 00 6A 07 00 00 00 00 00 81
        42 07 00 00 0A 07 00 00 70 07 00 00 00 00 00 81
        8C 07 00 00 0A 07 00 00 AC 07 00 00 00 00 00 81
        B8 07 00 00 0A 07 00 00 D8 07 00 00 00 00 00 81
        E8 07 00 00 0A 07 00 00 08 08 00 00 00 00 00 81
        18 08 00 00 0A 07 00 00 3A 08 00 00 00 00 00 81
        4A 08 00 00 0A 07 00 00 6C 08 00 00 00 00 00 81
        78 08 00 00 0A 07 00 00 9A 08 00 00 00 00 00 81
        AA 08 00 00 60 07 00 00 CC 08 00 00 00 00 00 81
        AA 08 00 00 0A 07 00 00 D2 08 00 00 00 00 00 81
        E6 08 00 00 0A 07 00 00 08 09 00 00 00 00 00 81
        14 09 00 00 0A 07 00 00 36 09 00 00 00 00 00 81
        42 09 00 00 0A 07 00 00 64 09 00 00 00 00 00 81
        78 09 00 00 60 07 00 00 9A 09 00 00 00 00 00 81
        78 09 00 00 0A 07 00 00 A0 09 00 00 08 00 00 00
        08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00
        21 00 01 00 28 00 01 00 28 00 01 00 28 00 01 00
        08 00 00 00 08 00 00 00 28 00 00 00 05 00 03 00
        00 00 00 00 00 00 28 00 00 00 01 00 00 00 28 00
        01 00 28 00 00 00 10 00 54 00 45 00 53 00 54 00
        54 00 45 00 53 00 54 00 14 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 00 00
        16 00 54 00 45 00 53 00 54 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 00 00 26 00 54 00 45 00
        53 00 54 00 54 00 45 00 53 00 54 00 54 00 45 00
        53 00 54 00 54 00 45 00 53 00 54 00 54 00 45 00
        53 00 05 00 01 00 00 00 00 00 00 00 1A 00 54 00
        45 00 53 00 54 00 54 00 45 00 53 00 54 00 54 00
        45 00 53 00 54 00 54 00 0A 00 54 00 45 00 53 00
        54 00 54 00 02 00 03 00 00 00 1E 00 54 00 45 00
        53 00 54 00 54 00 45 00 53 00 54 00 54 00 45 00
        53 00 54 00 54 00 5C 00 30 00 1E 00 54 00 54 00
        54 00 54 00 54 00 54 00 54 00 54 00 54 00 54 00
        54 00 54 00 54 00 54 00 54 00 00 00 4C 00 7B 00
        62 00 33 00 61 00 37 00 33 00 30 00 66 00 61 00
        2D 00 64 00 64 00 31 00 31 00 2D 00 34 00 33 00
        39 00 39 00 2D 00 38 00 36 00 61 00 61 00 2D 00
        65 00 65 00 63 00 37 00 39 00 37 00 34 00 61 00
        36 00 39 00 31 00 62 00 7D 00 00 00 1E 00 54 00
        45 00 53 00 54 00 54 00 45 00 53 00 54 00 54 00
        45 00 53 00 54 00 54 00 5C 00 31 00 00 00 4C 00
        7B 00 34 00 64 00 63 00 36 00 34 00 38 00 65 00
        36 00 2D 00 33 00 65 00 33 00 65 00 2D 00 34 00
        37 00 65 00 30 00 2D 00 61 00 62 00 66 00 37 00
        2D 00 62 00 32 00 66 00 39 00 61 00 65 00 62 00
        39 00 36 00 66 00 34 00 35 00 7D 00 00 00 1E 00
        54 00 45 00 53 00 54 00 54 00 45 00 53 00 54 00
        54 00 45 00 53 00 54 00 54 00 5C 00 32 00 00 00
        4C 00 7B 00 65 00 39 00 64 00 61 00 64 00 62 00
        31 00 64 00 2D 00 34 00 32 00 33 00 36 00 2D 00
        34 00 66 00 61 00 37 00 2D 00 61 00 31 00 38 00
        62 00 2D 00 62 00 64 00 30 00 30 00 38 00 62 00
        35 00 63 00 30 00 61 00 63 00 64 00 7D 00 00 00
        24 00 41 00 54 00 45 00 53 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 02 00 02 00 00 00 28 00 41 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        45 00 5C 00 30 00 00 00 4C 00 7B 00 32 00 65 00
        30 00 39 00 33 00 63 00 64 00 64 00 2D 00 65 00
        32 00 63 00 37 00 2D 00 34 00 35 00 34 00 36 00
        2D 00 62 00 64 00 65 00 30 00 2D 00 34 00 35 00
        65 00 64 00 37 00 35 00 65 00 38 00 37 00 64 00
        61 00 34 00 7D 00 00 00 28 00 41 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 45 00 5C 00
        31 00 00 00 4C 00 7B 00 35 00 32 00 35 00 31 00
        63 00 63 00 61 00 39 00 2D 00 64 00 62 00 31 00
        38 00 2D 00 34 00 32 00 61 00 65 00 2D 00 39 00
        39 00 65 00 39 00 2D 00 30 00 30 00 34 00 37 00
        33 00 34 00 34 00 30 00 36 00 33 00 31 00 63 00
        7D 00 00 00 14 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 02 00 11 00 00 00
        18 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 5C 00 30 00 12 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 02 00
        06 00 00 00 08 00 54 00 45 00 53 00 54 00 0A 00
        0C 00 01 0A 2B 06 01 04 01 82 37 0A 03 06 18 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 5C 00 31 00 02 00 06 00 00 00 18 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 5C 00 32 00 02 00 06 00 00 00 0A 00
        0C 00 01 0A 2B 06 01 04 01 82 37 3D 05 01 18 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 5C 00 33 00 02 00 06 00 00 00 0A 00
        22 00 03 0A 2B 06 01 04 01 82 37 0A 03 06 0A 2B
        06 01 04 01 82 37 0A 03 17 0A 2B 06 01 04 01 82
        37 0A 03 18 18 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 5C 00 34 00 02 00
        06 00 00 00 0A 00 22 00 03 0A 2B 06 01 04 01 82
        37 0A 03 06 0A 2B 06 01 04 01 82 37 0A 03 17 0A
        2B 06 01 04 01 82 37 0A 03 16 18 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 35 00 02 00 06 00 00 00 0A 00 0C 00 01 0A
        2B 06 01 04 01 82 37 4C 05 01 18 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 36 00 02 00 06 00 00 00 0A 00 0C 00 01 0A
        2B 06 01 04 01 82 37 3D 04 01 18 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 37 00 02 00 06 00 00 00 0A 00 0C 00 01 0A
        2B 06 01 04 01 82 37 0A 03 13 18 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 38 00 02 00 06 00 00 00 0A 00 0C 00 01 0A
        2B 06 01 04 01 82 37 0A 03 05 18 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 39 00 02 00 06 00 00 00 0A 00 0C 00 01 0A
        2B 06 01 04 01 82 37 0A 03 24 1A 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        5C 00 31 00 30 00 02 00 07 00 00 00 0A 00 0C 00
        01 0A 2B 06 01 04 01 82 37 4C 03 01 1A 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 45 00 53 00
        54 00 5C 00 31 00 31 00 02 00 07 00 00 00 0A 00
        0C 00 01 0A 2B 06 01 04 01 82 37 4C 0B 01 1A 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 5C 00 31 00 32 00 02 00 05 00 00 00
        0A 00 0C 00 01 0A 2B 06 01 04 01 82 37 4C 14 01
        1A 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 5C 00 31 00 33 00 02 00 08 00
        00 00 1A 00 54 00 45 00 53 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 5C 00 31 00 34 00 02 00
        0C 00 00 00 1A 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 5C 00 31 00 35 00
        02 00 0D 00 00 00 1A 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 5C 00 31 00
        36 00 02 00 07 00 00 00 0A 00 0C 00 01 0A 2B 06
        01 04 01 82 37 4C 08 01 1C 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 36 00 22 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 04 00 00 00 00 00
        03 00 00 00 00 00 0A 00 00 00 10 00 00 00 1C 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 5C 00 38 00 08 00 54 00
        45 00 53 00 54 00 02 00 04 80 00 00 04 00 00 00
        00 00 05 00 00 00 00 00 01 00 00 00 09 00 00 00
        0B 00 00 00 0C 00 00 00 1E 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 5C 00 31 00 31 00 04 00 00 00 00 00 01 00
        05 00 00 00 1E 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 5C 00
        31 00 32 00 04 00 00 00 00 00 02 00 00 00 00 00
        09 00 00 00 1E 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 5C 00
        31 00 34 00 04 00 00 00 00 00 02 00 03 00 00 00
        04 00 00 00 20 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 5C 00
        31 00 32 00 38 00 04 00 00 00 00 00 02 00 00 00
        00 00 09 00 00 00 20 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 45 00 53 00
        5C 00 31 00 32 00 39 00 04 00 00 00 00 00 01 00
        02 00 00 00 20 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 5C 00
        31 00 33 00 30 00 04 00 00 00 00 00 02 00 06 00
        00 00 0B 00 00 00 20 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 54 00 45 00 53 00
        5C 00 31 00 33 00 31 00 02 00 04 80 00 00 04 00
        00 00 00 00 03 00 00 00 00 00 08 00 00 00 09 00
        00 00 20 00 54 00 45 00 53 00 54 00 45 00 53 00
        54 00 45 00 53 00 54 00 45 00 53 00 5C 00 31 00
        33 00 32 00 04 00 00 00 00 00 01 00 07 00 00 00
        20 00 54 00 45 00 53 00 54 00 45 00 53 00 54 00
        45 00 53 00 54 00 45 00 53 00 5C 00 31 00 33 00
        33 00 04 00 00 00 00 00 01 00 07 00 00 00 20 00
        54 00 45 00 53 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 5C 00 31 00 33 00 34 00
        04 00 00 00 00 00 03 00 00 00 00 00 08 00 00 00
        09 00 00 00 20 00 54 00 45 00 53 00 54 00 45 00
        53 00 54 00 45 00 53 00 54 00 45 00 53 00 5C 00
        31 00 33 00 35 00 02 00 04 80 00 00 04 00 00 00
        00 00 05 00 00 00 00 00 01 00 00 00 08 00 00 00
        0E 00 00 00 0F 00 00 00""")

    def test_basic_decode(self):
        inp = io.BytesIO(FirmwarePolicyTest.TEST_DEVICEID_C2E28)
        policyManuf = FirmwarePolicy(inp)
        policyManuf.Print()
        self.assertEqual(policyManuf.RulesCount, 1)
        self.assertEqual(policyManuf.Rules[0].RootKey, int(0x81000000))
        self.assertEqual(policyManuf.Rules[0].SubKeyName.String, "Debug")
        self.assertEqual(policyManuf.Rules[0].ValueName.String, "DeviceID")
        self.assertEqual(policyManuf.Rules[0].Value.valueType.vt, 5)
        self.assertEqual(policyManuf.Rules[0].Value.value, int(0xc2e28c3a948caef6))

    def test_basic_create_encode_decode_roundtrip(self):
        policyManuf = FirmwarePolicy()
        nonce = secrets.randbits(64)
        TargetInfo = {
            # EV Certificate Subject CN="<foo>", recommend matches SmbiosSystemManufacturer,
            # SMBIOS Table 1, offset 04h (System Manufacturer)
            'Manufacturer': 'Contoso Computers, LLC',
            # SmbiosSystemProductName, SMBIOS Table 1, offset 05h (System Product Name)
            'Product': 'Laptop Foo',
            # SmbiosSystemSerialNumber, SMBIOS System Information (Type 1 Table) -> Serial Number
            'SerialNumber': 'F0013-000243546-X02',
            # Yours to define, or not use (NULL string), ODM name is suggested
            'OEM_01': 'ODM Foo',
            # Yours to define, or not use (NULL string)
            'OEM_02': '',
            # The following is randomly generated by the device
            'Nonce': nonce}
        policyManuf.SetDeviceTarget(TargetInfo)

        policy = \
            FirmwarePolicy.FW_POLICY_VALUE_ACTION_SECUREBOOT_CLEAR \
            + FirmwarePolicy.FW_POLICY_VALUE_ACTION_TPM_CLEAR
        policyManuf.SetDevicePolicy(policy=policy)

        first_output = io.BytesIO()
        policyManuf.SerializeToStream(stream=first_output)
        policyManuf.Print()

        first_output.seek(0)
        testPolicy = FirmwarePolicy(fs=first_output)
        second_output = io.BytesIO()
        testPolicy.SerializeToStream(stream=second_output)

        self.assertEqual(first_output.getbuffer(), second_output.getbuffer())

        first_output.close()
        second_output.close()

# The below tests exercise larger error paths and code not normally travelled

    def test_legacy_decode(self):
        # This policy includes rules where SubKeyOffsets and ValueNameOffsets are reused
        # Reserved2 fields are included as well
        inp = io.BytesIO(FirmwarePolicyTest.TEST_LEGACY_POLICY)
        legacyPolicy = FirmwarePolicy(inp)
        legacyPolicy.Print()
        self.assertEqual(legacyPolicy.RulesCount, 56)
        self.assertEqual(legacyPolicy.Reserved2Count, 17)

    def test_invalid_policyvaluetype(self):
        invalidPolicy = PolicyValueType(Type=42)
        testArray = bytearray()
        invalidPolicy.Serialize(valueOut=testArray)

        testStream = io.BytesIO(testArray)
        invalidPolicy2 = PolicyValueType.FromFileStream(fs=testStream)

        self.assertEqual(invalidPolicy.vt, invalidPolicy2.vt)

    def test_basic_reserved(self):
        # default constructor
        r1 = Reserved2()
        outArray1 = bytearray()
        r1.Serialize(ruleOut=outArray1)

        # constructor from filestream
        zeroObjectStream = io.BytesIO(outArray1)
        r2 = Reserved2(fs=zeroObjectStream, vtoffset=0)
        outArray2 = bytearray()
        r2.Serialize(ruleOut=outArray2)
        r2.Print()

        self.assertEqual(outArray1, outArray2)
        self.assertEqual(r1.ObjectType, r2.ObjectType)
        self.assertEqual(r1.Element, r2.Element)
        self.assertEqual(r1.OffsetToValue, r2.OffsetToValue)
        self.assertEqual(r1.ObjectType, 0)
        self.assertEqual(r1.Element, 0)
        self.assertEqual(r1.OffsetToValue, 0)

        # Test in a policy
        policy = FirmwarePolicy()
        # no need to add a Reserved1, the code won't try to deserialize or serialize it
        policy.Reserved1Count += 1
        policy.Reserved2.append(r2)
        policy.Reserved2Count += 1
        outArray3 = bytearray()
        policy.Serialize(output=outArray3)
        policy.Print()
        # There is no value to test, not throwing an exception is sufficient
