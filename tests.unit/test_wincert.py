import unittest
import io

from edk2toollib.uefi.authenticated_variables_structure_support import EfiTime
from edk2toollib.uefi.wincert import WinCert, WinCertPkcs1, WinCertUefiGuid
from edk2toollib.tests.testdata.certificate_blobs import SHA256_FINGERPRINT, TEST_AUTH_VAR_PKCS7


class WinCertPkcs1Tests(unittest.TestCase):
    """Tests WinCertPkcs1"""

    def test_add_cert_data_raises_exceptions(self):
        """Tests add cert data and exceptions"""
        # Create a WinCertPkcs1 Object
        wincert = WinCertPkcs1()

        # Attempt to add Cert Data and capture the error
        with self.assertRaises(ValueError) as context:
            wincert.add_cert_data(fs=None)

        self.assertTrue("You must set the Hash Algorithm first" in str(context.exception))

        # Set the hash algorithm
        wincert.set_hash_algorithm(WinCertPkcs1.EFI_HASH_SHA256)

        # If this raises an exception the test will implictly fail
        with io.BytesIO(bytes.fromhex(SHA256_FINGERPRINT)) as f:
            wincert.add_cert_data(f)

            # Attempt to add Cert Data and capture the error
            with self.assertRaises(ValueError) as context:
                wincert.add_cert_data(f)

    def test_write_and_from_filestream(self):
        """Tests write and from filestream"""
        # Create a WinCertPkcs1 Object
        wincert0 = WinCertPkcs1()

        # Set the hash algorithm
        wincert0.set_hash_algorithm(WinCertPkcs1.EFI_HASH_SHA256)

        with io.BytesIO(bytes.fromhex(SHA256_FINGERPRINT)) as f:
            wincert0.add_cert_data(f)
        
        # write to a filestream
        with io.BytesIO() as f0, io.BytesIO() as f1, io.BytesIO() as f2:
            
            # Write the data to the first filestream
            wincert0.write(f0)

            # Seek to the start
            f0.seek(0)

            # Create a new wincert object from the first filestream
            wincert1 = WinCertPkcs1(f0)

            # Write the data to the second filestream
            wincert1.write(f1)

            # Seek to the start
            f0.seek(0)
            f1.seek(0)

            # Did we write the same data?
            self.assertEqual(f0.getvalue(), f1.getvalue())

            # Create an empty wincert
            wincert2 = WinCertPkcs1()

            # Seek to the start
            f0.seek(0)
            f1.seek(0)

            # populate the wincert from the previous filestream
            wincert2.decode(f1)

            # write to a new filestream
            wincert2.write(f2)

            # Seek to the start
            f1.seek(0)
            f2.seek(0)

            # Compare the data
            self.assertEqual(f0.getvalue(), f2.getvalue())

    def test_write_and_print(self):
        """Tests write and print"""
        wincert_header = "-------------------- WinCertPKCS115 ---------------------"
        # Create a WinCertPkcs1 Object
        wincert0 = WinCertPkcs1()

        # Set the hash algorithm
        wincert0.set_hash_algorithm(WinCertPkcs1.EFI_HASH_SHA256)
        with io.BytesIO(bytes.fromhex(SHA256_FINGERPRINT)) as f:
            wincert0.add_cert_data(f)

        # Emulate std out
        with io.StringIO() as out:
            wincert0.print(out)
            out.seek(0)
            self.assertTrue(wincert_header in out.read())


class WinCertUefiGuidTest(unittest.TestCase):

    def test_add_cert_data_raises_exceptions(self):

        wincert = WinCertUefiGuid()

        # Attempt to add Cert Data and capture the error
        with self.assertRaises(ValueError) as context:
            wincert.add_cert_data(None)
        
        self.assertTrue("Invalid datatype provided" in str(context.exception))

        # TEST_SIGNATURE_PKCS7 is a signed variable, so we need to remove data we don't need for this test
        test_data = bytes.fromhex(TEST_AUTH_VAR_PKCS7)

        with io.BytesIO(test_data) as f:
            # Remove EfiTime field from the beginning of the filestream
            _ = EfiTime(f)
            wincert.add_cert_data(f)

        old_length = wincert.get_length()

        with io.BytesIO(test_data) as f:
            wincert.add_cert_data(f)

        self.assertTrue(old_length == wincert.get_length())

    def test_write_encode_and_decode(self):
        """Tests, write,encode, decode and dump_info"""
        wincert0 = WinCertUefiGuid()

        # TEST_SIGNATURE_PKCS7 is a signed variable, so we need to remove data we don't need for this test
        test_data = bytes.fromhex(TEST_AUTH_VAR_PKCS7)
        
        # ignoring the top of the binary data and the bottom we can extract the wincert
        with io.BytesIO(test_data) as f:
            _ = EfiTime(decodefs=f)
            wincert0.decode(f)
            # anything left over would be the binary data but for us we don't care

        # try to dump the info from the certificate, doing so will parse the signature data and confirm
        # it's a valid signature
        with io.StringIO() as out:
            wincert0.dump_info(outfs=out)

            output = out.getvalue()
            self.assertTrue("SignedData" in output)
            self.assertTrue("WIN_CERTIFICATE" in output)

        wincert1 = WinCertUefiGuid()

        # encode the original object
        encoded = wincert0.encode()
        # Can we decode it from the bytes
        wincert1.decode(encoded)

        # encode / decode work
        self.assertTrue(wincert1.encode(), encoded)
        
        # Test write - which is basically just an encode
        with io.BytesIO() as wincert1_encode:
            wincert1.write(wincert1_encode)

            self.assertTrue(wincert1.encode(), wincert1_encode)

    def test_add_cert_data(self):
        """"Tests add_cert_data, get_certificate, dump_info and string"""
        wincert0 = WinCertUefiGuid()

        # TEST_SIGNATURE_PKCS7 is a signed variable, so we need to remove data we don't need for this test
        test_data = bytes.fromhex(TEST_AUTH_VAR_PKCS7)
        
        # ignoring the top of the binary data and the bottom we can extract the wincert
        with io.BytesIO(test_data) as f:
            _ = EfiTime(decodefs=f)
            wincert0.decode(f)
            # anything left over would be the binary data but for us we don't care

        # encode the original object
        encoded = wincert0.encode()

        # create a new wincert
        wincert1 = WinCertUefiGuid()

        # test adding cert data as a buffer
        wincert1.add_cert_data(wincert0.get_certificate())

        with io.StringIO() as out:
            wincert1.dump_info(outfs=out)

            output = out.getvalue()
            self.assertTrue("SignedData" in output)
            self.assertTrue("WIN_CERTIFICATE" in output)

        self.assertTrue(wincert1.encode(), encoded)

        # test adding cert data as a filestream
        # create a new wincert
        wincert2 = WinCertUefiGuid()

        with io.BytesIO(wincert1.get_certificate()) as f:
            wincert2.add_cert_data(f)

        with io.StringIO() as out:
            wincert2.dump_info(outfs=out)

            output = out.getvalue()
            self.assertTrue("SignedData" in output)
            self.assertTrue("WIN_CERTIFICATE" in output)

        wincert_string = str(wincert2)
        self.assertTrue("SignedData" in wincert_string)
        self.assertTrue("WIN_CERTIFICATE" in wincert_string)


class WinCertTests(unittest.TestCase):

    def test_factory(self):
        wincert_guid_type = WinCertUefiGuid()
        # TEST_SIGNATURE_PKCS7 is a signed variable, so we need to remove data we don't need for this test
        test_data = bytes.fromhex(TEST_AUTH_VAR_PKCS7)
        
        # ignoring the top of the binary data and the bottom we can extract the wincert
        with io.BytesIO(test_data) as f:
            _ = EfiTime(decodefs=f)
            wincert_guid_type.decode(f)

        wincert_pkcs1_type = WinCertPkcs1()
        wincert_pkcs1_type.set_hash_algorithm(WinCertPkcs1.EFI_HASH_SHA256)
        with io.BytesIO(bytes.fromhex(SHA256_FINGERPRINT)) as f:
            wincert_pkcs1_type.add_cert_data(f)
        
        with io.BytesIO(wincert_guid_type.encode()) as f:
            wincert = WinCert().factory(f)

            self.assertTrue(wincert_guid_type.encode(), wincert.encode())
            self.assertTrue(type(wincert), type(wincert_guid_type))

        with io.BytesIO(wincert_pkcs1_type.encode()) as f:
            wincert = WinCert().factory(f)

            self.assertTrue(wincert_pkcs1_type.encode(), wincert.encode())
            self.assertTrue(type(wincert), type(wincert_pkcs1_type))

            
if __name__ == "__main__":
    unittest.main()
