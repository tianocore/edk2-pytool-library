import unittest

from edk2toollib.uefi.status_codes import UefiStatusCode

class TestUefiStatusCodes (unittest.TestCase):

    def test_Hex64ToString (self):

        StatusCode = "0x0000000000000000"

        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Success")

        StatusCode = "0x800000000000000E"

        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Not Found")

        StatusCode = "0x8000000000000024"

        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Undefined StatusCode")

# python -m unittest status_codes_test.py