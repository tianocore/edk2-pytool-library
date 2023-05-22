##
# UEFI Authenticated Variable Structure Support Library
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module containing Authenticated Variable Structure definitions based on UEFI specification (2.7).

Each object can be created and or populated from a file stream.
Each object can be written to a filesteam as binary and printed to the console in text.
"""
import logging
import datetime
import struct
import hashlib
import uuid
import io
import sys

from typing import BinaryIO, List
from operator import attrgetter

from warnings import warn

from abc import ABC, abstractmethod

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import pkcs7, Encoding
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.base import Certificate

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1_modules import rfc2315

from edk2toollib.uefi.wincert import WinCert, WinCertUefiGuid
from edk2toollib.utility_functions import hexdump
from edk2toollib.uefi.uefi_multi_phase import EfiVariableAttributes


# spell-checker: ignore decodefs, createfs, deduplicated, deduplication

# UEFI global Variable Namespace
EfiGlobalVarNamespaceUuid = uuid.UUID('8BE4DF61-93CA-11d2-AA0D-00E098032B8C')
Sha256Oid = [0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01]


class CommonUefiStructure(ABC):
    """This structure contains the methods common across all UEFI Structures."""

    def __init__(self):
        """Inits the object."""
        pass

    @abstractmethod
    def write(self, fs: BinaryIO) -> None:
        """Writes the object to a filestream.

        Args:
            fs (BinaryIO): a filestream object to write the object to
        """
        pass

    @abstractmethod
    def decode(self, fs: BinaryIO, decodesize: int) -> None:
        """Populates the object from a filestream.

        Args:
            fs (BinaryIO | Bytes): a filestream object to read from
            decodesize (int): number of bytes to decode as the object
        """
        pass

    @abstractmethod
    def encode(self) -> bytes:
        """Returns the object as a binary object.

        Returns:
            bytes: a binary object of the object
        """
        pass

    @abstractmethod
    def print(self, outfs=sys.stdout) -> None:
        """Prints the object to the console."""
        pass


class EfiSignatureDataEfiCertX509(CommonUefiStructure):
    """An object representing a EFI_SIGNATURE_DATA Structure for X509 Certs."""
    STATIC_STRUCT_SIZE = 16
    FIXED_SIZE = False

    def __init__(self,
                 decodefs: BinaryIO = None,
                 decodesize=0,
                 createfs: BinaryIO = None,
                 cert: bytes = None,
                 sigowner: uuid.UUID = None):
        """Inits the object.

        Args:
            decodefs (BinaryIO): a filestream object of binary content that is the structure encoded
            decodesize (int):number of bytes to decode as the EFI_SIGNATURE_DATA object (guid + x509 data)
            createfs (BinaryIO): a filestream object that is the DER encoded x509 cert
            cert (bytes): the x509 certificate to initialize this object
            sigowner (uuid.UUID): the uuid object of the signature owner guid

        Raises:
            (ValueError): Invalid FileStream size
            (ValueError): Invalid Parameters
        """
        if (decodefs is not None):
            self.decode(decodefs, decodesize)
        elif (createfs is not None):
            # create a new one
            self.signature_owner = sigowner
            # should be 0 but maybe this filestream has other things at the head
            start = createfs.tell()
            createfs.seek(0, 2)
            end = createfs.tell()
            createfs.seek(start)
            self.signature_data_size = end - start
            if (self.signature_data_size < 0):
                raise ValueError("Create File Stream has invalid size")
            self.signature_data = (createfs.read(self.signature_data_size))
        elif (cert is not None):
            self.signature_owner = sigowner
            self.signature_data_size = len(cert)
            self.signature_data = cert

        else:
            raise ValueError("Invalid Parameters - Not Supported")

    @property
    def SignatureOwner(self) -> uuid.UUID:
        """Returns the Signature Owner as a uuid object."""
        warn("SignatureOwner is deprecated. Use signature_owner instead.", DeprecationWarning, 2)
        return self.signature_owner

    @SignatureOwner.setter
    def SignatureOwner(self, value: uuid.UUID) -> None:
        """Sets the Signature Owner from a uuid object."""
        warn("SignatureOwner is deprecated. Use signature_owner instead.", DeprecationWarning, 2)
        self.signature_owner = value

    def __lt__(self, other):
        """Less-than comparison for sorting. Looks at signature_data only, not signature_owner."""
        return self.signature_data < other.signature_data

    def PopulateFromFileStream(self, fs: BinaryIO, decodesize):
        """Decodes an object from a filestream.

        Args:
            fs (BinaryIO): filestream
            decodesize (int): amount to decode.

        Raises:
            (ValueError): Invalid filestream
            (ValueError): Invalid Decode Size
        """
        warn("PopulateFromFileStream() is deprecated. Use decode() instead.", DeprecationWarning, 2)
        self.decode(fs, decodesize=decodesize)

    def decode(self, fs: BinaryIO, decodesize):
        """Decodes an object from a filestream.

        Args:
            fs (BinaryIO): filestream
            decodesize (int): amount to decode.

        Raises:
            (ValueError): Invalid filestream
            (ValueError): Invalid Decode Size
        """
        if fs is None:
            raise ValueError("Invalid File Steam")

        if decodesize == 0:
            raise ValueError("Invalid Decode Size")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if (end - offset) < EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE:  # size of the  guid
            raise ValueError("Invalid file stream size")

        if (end - offset) < decodesize:  # size requested is too big
            raise ValueError("Invalid file stream size vs decodesize")

        self.signature_owner = uuid.UUID(bytes_le=fs.read(16))

        # read remaining decode size for x509 data
        self.signature_data_size = decodesize - \
            EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE
        self.signature_data = fs.read(self.signature_data_size)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated. Use print() instead.", DeprecationWarning, 2)
        self.print(compact=compact, outfs=outfs)

    def print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureData - EfiSignatureDataEfiCertX509\n")
            outfs.write(f"  Signature Owner:      {str(self.signature_owner)}\n")
            outfs.write("  Signature Data: \n")
            if (self.signature_data is None):
                outfs.write("    NONE\n")
            else:
                sdl = self.signature_data
                if self.signature_data_size != len(sdl):
                    raise ValueError(
                        "Invalid Signature Data Size vs Length of data")
                hexdump(sdl, outfs=outfs)
        else:
            s = "ESD:EFI_CERT_X509,"
            s += f"{str(self.signature_owner)},"
            if (self.signature_data is None):
                s += 'NONE'
            else:
                sdl = self.signature_data
                for index in range(len(sdl)):
                    s += f'{sdl[index]:02X}'
            outfs.write(s)
            outfs.write("\n")

    def Write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (ValueError): Invalid filestream
            (ValueError): Invalid object
        """
        warn("Write() is deprecated. Use write() instead.", DeprecationWarning, 2)
        self.write(fs)

    def write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (ValueError): Invalid filestream
            (ValueError): Invalid object
        """
        if fs is None:
            raise ValueError("Invalid File Output Stream")
        if self.signature_data is None:
            raise ValueError("Invalid object")

        fs.write(self.encode())

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        warn("GetBytes() is deprecated. Use encode() instead.", DeprecationWarning, 2)
        return self.encode()

    def encode(self) -> bytes:
        """Return bytes array produced by Write()."""
        return self.signature_owner.bytes_le + self.signature_data

    def GetTotalSize(self):
        """Returns the total size of the object."""
        warn("GetTotalSize() is deprecated. Use get_total_size() instead.", DeprecationWarning, 2)
        return self.get_total_size()

    def get_total_size(self):
        """Returns the total size of the object."""
        return EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE + self.signature_data_size


class EfiSignatureDataEfiCertSha256(CommonUefiStructure):
    """An object representing a EFI_SIGNATURE_DATA Structure for Sha256 Certs."""
    STATIC_STRUCT_SIZE = 16 + hashlib.sha256().digest_size  # has guid and array
    FIXED_SIZE = True

    def __init__(self,
                 decodefs: BinaryIO = None,
                 createfs: BinaryIO = None,
                 digest: bytes = None,
                 sigowner: uuid = None):
        """Inits the object.

        Args:
            decodefs (BinaryIO): a filestream object of binary content that is the structure encoded
            createfs (BinaryIO): a filestream object that is the DER encoded x509 cert
            digest (bytes): a bytes object that contains the hash value for new signature data
            sigowner (uuid.UUID): the uuid object of the signature owner guid

        Raises:
            (Exception): Invalid FileStream size
            (ValueError): Invalid Parameters
        """
        if decodefs is not None:
            self.decode(decodefs)
        elif (createfs is not None):
            # create a new one
            self.signature_owner = sigowner
            self.signature_data = (hashlib.sha256(createfs.read()).digest())
        elif digest is not None:
            digest_length = len(digest)
            if digest_length != hashlib.sha256().digest_size:
                raise Exception("Invalid digest length (found / expected): (%d / %d)",
                                digest_length, hashlib.sha256().digest_size)
            self.signature_owner = sigowner
            self.signature_data = digest
        else:
            raise ValueError("Invalid Parameters - Not Supported")

    def decode(self, fs, decodesize: int = -1):
        """Decodes an object from a filestream.

        Args:
            fs (BinaryIO): filestream
            decodesize (int): size of the object to decode (UNUSED)

        Raises:
            (Exception): Invalid filestream
        """
        if fs is None:
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if (end - offset) < EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE:  # size of the  data
            raise Exception("Invalid file stream size")

        self.signature_owner = uuid.UUID(bytes_le=fs.read(16))

        self.signature_data = fs.read(hashlib.sha256().digest_size)

    def PopulateFromFileStream(self, fs):
        """Loads an object from a filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
        """
        warn("PopulateFromFileStream() is deprecated. Use decode() instead.", DeprecationWarning, 2)
        self.decode(fs)

    def print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureData - EfiSignatureDataEfiCertSha256\n")
            outfs.write(f"  Signature Owner:      {str(self.signature_owner)}\n")
            outfs.write("  Signature Data: ")
            if (self.signature_data is None):
                outfs.write(" NONE\n")
            else:
                sdl = self.signature_data
                for index in range(len(sdl)):
                    outfs.write(f"{sdl[index]:02X}")
                outfs.write("\n")
        else:
            s = 'ESD:EFI_CERT_SHA256,'
            s += f"{str(self.signature_owner)},"
            if (self.signature_data is None):
                s += 'NONE'
            else:
                sdl = self.signature_data
                for index in range(len(sdl)):
                    s += f"{sdl[index]:02X}"
            outfs.write(s)
            outfs.write("\n")

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated. Use print() instead.", DeprecationWarning, 2)
        self.print(compact, outfs)

    def write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid object
        """
        if fs is None:
            raise Exception("Invalid File Output Stream")
        if self.signature_data is None:
            raise Exception("Invalid object")

        fs.write(self.signature_owner.bytes_le)
        fs.write(self.signature_data)

    def Write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid object
        """
        warn("Write() is deprecated. Use write() instead.", DeprecationWarning, 2)
        self.write(fs)

    def encode(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        warn("GetBytes() is deprecated. Use encode() instead.", DeprecationWarning, 2)
        return self.encode()

    def get_total_size(self):
        """Returns the total size of the object."""
        return EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE

    def GetTotalSize(self):
        """Returns the total size of the object."""
        warn("GetTotalSize() is deprecated. Use get_total_size() instead.", DeprecationWarning, 2)
        return self.get_total_size()


class EfiSignatureHeader(object):  # noqa
    def __init__(self, fs, header_size):  # noqa
        raise Exception("Not Implemented")


class EfiSignatureDataFactory(object):
    """Factory class for generating an EFI Signature struct."""
    EFI_CERT_SHA256_GUID = uuid.UUID('c1c41626-504c-4092-aca9-41f936934328')
    # EFI_CERT_RSA2048_GUID = uuid.UUID("0x3c5766e8, 0x269c, 0x4e34, 0xaa, 0x14, 0xed, 0x77, 0x6e, 0x85, 0xb3, 0xb6")
    # EFI_CERT_RSA2048_SHA256_GUID = uuid.UUID("0xe2b36190, 0x879b, 0x4a3d, 0xad, 0x8d, 0xf2, 0xe7, 0xbb, 0xa3, 0x27, 0x84")  # noqa: E501
    # EFI_CERT_SHA1_GUID = uuid.UUID("0x826ca512, 0xcf10, 0x4ac9, 0xb1, 0x87, 0xbe, 0x1, 0x49, 0x66, 0x31, 0xbd")
    # EFI_CERT_RSA2048_SHA1_GUID = uuid.UUID("0x67f8444f, 0x8743, 0x48f1, 0xa3, 0x28, 0x1e, 0xaa, 0xb8, 0x73, 0x60, 0x80")    # noqa: E501
    EFI_CERT_X509_GUID = uuid.UUID("a5c059a1-94e4-4aa7-87b5-ab155c2bf072")
    # EFI_CERT_SHA224_GUID = uuid.UUID("0xb6e5233, 0xa65c, 0x44c9, 0x94, 0x7, 0xd9, 0xab, 0x83, 0xbf, 0xc8, 0xbd")
    # EFI_CERT_SHA384_GUID = uuid.UUID("0xff3e5307, 0x9fd0, 0x48c9, 0x85, 0xf1, 0x8a, 0xd5, 0x6c, 0x70, 0x1e, 0x1")
    # EFI_CERT_SHA512_GUID = uuid.UUID("0x93e0fae, 0xa6c4, 0x4f50, 0x9f, 0x1b, 0xd4, 0x1e, 0x2b, 0x89, 0xc1, 0x9a")
    EFI_CERT_X509_SHA256_GUID = uuid.UUID(
        "3bd2a492-96c0-4079-b420-fcf98ef103ed")
    # EFI_CERT_X509_SHA384_GUID = uuid.UUID("0x7076876e, 0x80c2, 0x4ee6, 0xaa, 0xd2, 0x28, 0xb3, 0x49, 0xa6, 0x86, 0x5b")     # noqa: E501
    # EFI_CERT_X509_SHA512_GUID = uuid.UUID("0x446dbf63, 0x2502, 0x4cda, 0xbc, 0xfa, 0x24, 0x65, 0xd2, 0xb0, 0xfe, 0x9d")     # noqa: E501
    # EFI_CERT_TYPE_PKCS7_GUID = uuid.UUID("0x4aafd29d, 0x68df, 0x49ee, 0x8a, 0xa9, 0x34, 0x7d, 0x37, 0x56, 0x65, 0xa7")

    @staticmethod
    def factory(fs: BinaryIO, type, size):
        """This method is a factory for creating the correct Efi Signature Data object from the filestream.

        Uses a Filestream of an existing auth payload.

        Args:
            fs (BinaryIO): filestream to read
            type (uuid.UUID): Guid of the type
            size (int): decodesize for x509, struct size for Sha256
        """
        if (fs is None):
            raise Exception("Invalid File stream")

        if (type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            if (size != EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE):
                raise Exception("Invalid Size 0x%x" % size)
            return EfiSignatureDataEfiCertSha256(decodefs=fs)

        elif (type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(decodefs=fs, decodesize=size)

        else:
            logging.error("GuidType Value: %s" % type)
            raise Exception("Not Supported")

    @staticmethod
    def Factory(fs: BinaryIO, type, size):
        """This method is a factory for creating the correct Efi Signature Data object from the filestream.

        Uses a Filestream of an existing auth payload.

        Args:
            fs (BinaryIO): filestream to read
            type (uuid.UUID): Guid of the type
            size (int): decodesize for x509, struct size for Sha256
        """
        warn("Factory() is deprecated, use factory() instead", DeprecationWarning)
        return EfiSignatureDataFactory.factory(fs, type, size)

    @staticmethod
    def Create(type, ContentFileStream, sigowner):
        """Create a new EFI Sginature Data Object.

        Args:
            type (uuid.UUID): Guid of the type
            ContentFileStream (BinaryIO): filestream to read
            sigowner (uuid.UUID): the uuid object of the signature owner guid
        """
        warn("Create() is deprecated, use create() instead", DeprecationWarning, 2)
        return EfiSignatureDataFactory.create(type, ContentFileStream, sigowner)

    @staticmethod
    def create(type, ContentFileStream, sigowner):
        """Create a new EFI Sginature Data Object.

        Args:
            type (uuid.UUID): Guid of the type
            ContentFileStream (BinaryIO): filestream to read
            sigowner (uuid.UUID): the uuid object of the signature owner guid
        """
        if (ContentFileStream is None):
            raise Exception("Invalid Content File Stream")

        if (type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            return EfiSignatureDataEfiCertSha256(createfs=ContentFileStream, sigowner=sigowner)
        elif (type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(createfs=ContentFileStream, sigowner=sigowner)
        else:
            raise Exception("Not Supported")


class EfiSignatureList(CommonUefiStructure):
    """An object representing a EFI_SIGNATURE_LIST."""
    STATIC_STRUCT_SIZE = 16 + 4 + 4 + 4

    def __init__(self, filestream: BinaryIO = None, typeguid: uuid.UUID = None):
        """Inits the object.

        Args:
            filestream (:obj:`BinaryIO`, optional): a filestream object of binary content that is the structure encoded
            typeguid (:obj:`uuid.UUID`, optional): type guid
        """
        if (filestream is None):

            # Type of the signature. GUID signature types are defined in below.
            self.signature_type = typeguid

            # Total size of the signature list, including this header.
            self.signature_list_size = EfiSignatureList.STATIC_STRUCT_SIZE

            # Size of the signature header which precedes the array of signatures.
            self.signature_header_size = -1

            # Size of each signature.
            self.signature_size = 0

            # Header before the array of signatures. The format of this header is specified by the signature_type.
            self.signature_header = None

            # An array of signatures. Each signature is signature_size bytes in length.
            self.signature_data_list = None

        else:
            self.decode(filestream)

    def decode(self, fs: BinaryIO):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
            (Exception): Invalid siglist
            (Exception): Invalid parsing
        """
        if fs is None:
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if (end - start) < EfiSignatureList.STATIC_STRUCT_SIZE:  # size of the static header data
            raise Exception("Invalid file stream size")

        self.signature_type = uuid.UUID(bytes_le=fs.read(16))
        self.signature_list_size = struct.unpack("<I", fs.read(4))[0]
        self.signature_header_size = struct.unpack("<I", fs.read(4))[0]
        self.signature_size = struct.unpack("<I", fs.read(4))[0]

        # check the total size of this is within the File
        if ((end - start) < self.signature_list_size):
            logging.debug(f"signature_list_size {self.signature_list_size:0x}")
            logging.debug(f"End - Start is {(end - start):0x}")
            raise Exception(
                "Invalid File Stream.  Not enough file content to cover the Sig List Size")

        # check that structure is built correctly and there is room within the structure total size to read the header
        if ((self.signature_list_size - (fs.tell() - start)) < self.signature_header_size):
            raise Exception("Invalid Sig List.  Sizes not correct.  "
                            "signature_header_size extends beyond end of structure")

        # Signature Header is allowed to be nothing (size 0)
        self.signature_header = None
        if (self.signature_header_size > 0):
            self.signature_header = EfiSignatureHeader(
                fs, self.signature_header_size)

        if (((self.signature_list_size - (fs.tell() - start)) % self.signature_size) != 0):
            raise Exception(
                "Invalid Sig List.  Signature Data Array is not a valid size")

        self.signature_data_list = []
        while (start + self.signature_list_size) > fs.tell():
            # double check that everything is adding up correctly.
            if (start + self.signature_list_size - fs.tell() - self.signature_size) < 0:
                raise Exception(
                    "Invalid Signature List Processing.  Signature Data not correctly parsed!!")
            a = EfiSignatureDataFactory.factory(
                fs, self.signature_type, self.signature_size)
            self.signature_data_list.append(a)

    def PopulateFromFileStream(self, fs: BinaryIO):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
            (Exception): Invalid siglist
            (Exception): Invalid parsing
        """
        warn("PopulateFromFileStream() is deprecated, use decode() instead.", DeprecationWarning, 2)
        self.decode(fs)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated, use print() instead().", DeprecationWarning, 2)
        self.print(compact=compact, outfs=outfs)

    def print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureList\n")
            outfs.write(f"  Signature Type:        {str(self.signature_type)}\n")
            outfs.write(f"  Signature List Size:   {self.signature_list_size:0x}\n")
            outfs.write(f"  Signature Header Size: {self.signature_header_size:0x}\n")
            outfs.write(f"  Signature Size:       {self.signature_size:0x}\n")
            if (self.signature_header is not None):
                self.signature_header.print(compact=compact, outfs=outfs)
            else:
                outfs.write("  Signature Header:      NONE\n")
        else:
            csv = "ESL:"
            csv += f"{str(self.signature_type)}"
            csv += f",{self.signature_list_size:0x}"
            csv += f",{self.signature_header_size:0x}"
            csv += f",{self.signature_size:0x}"
            if (self.signature_header is not None):
                csv += self.signature_header.print(compact=compact, outfs=outfs)
            else:
                csv += ",NONE"
            outfs.write(csv)
            outfs.write('\n')

        if (self.signature_data_list is not None):
            for a in self.signature_data_list:
                a.print(compact=compact, outfs=outfs)

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
            (Exception): Uninitialized Sig header
        """
        warn("Write() is deprecated, use write() instead", DeprecationWarning, 2)
        self.write(fs)

    def write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
            (Exception): Uninitialized Sig header
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        if ((self.signature_header is None) and (self.signature_header_size == -1)):
            raise Exception("Invalid object.  Uninitialized Sig Header")

        fs.write(self.signature_type.bytes_le)
        fs.write(struct.pack("<I", self.signature_list_size))
        fs.write(struct.pack("<I", self.signature_header_size))
        fs.write(struct.pack("<I", self.signature_size))
        if (self.signature_header is not None):
            self.signature_header.write(fs)

        if (self.signature_data_list is not None):
            for a in self.signature_data_list:
                a.write(fs)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        warn("GetBytes() is deprecated, use encode() instead.", DeprecationWarning, 2)
        return self.encode()

    def encode(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.write(fs)
            return fs.getvalue()

    def AddSignatureHeader(self, SigHeader, SigSize=0):
        """Adds the Signature Header.

        Raises:
            (Exception): Signature header already set
        """
        if (self.signature_header is not None):
            raise Exception("Signature Header already set")

        if (self.signature_header_size != -1):
            raise Exception("Signature Header already set (size)")

        if (self.signature_size != 0):
            raise Exception("Signature Size already set")

        if (self.signature_data_list is not None):
            raise Exception("Signature Data List is already initialized")

        self.signature_header = SigHeader
        if (SigHeader is None):
            self.signature_header_size = 0
            self.signature_size = SigSize
        else:
            self.signature_header_size = SigHeader.get_total_size()
            self.signature_size = SigHeader.GetSizeOfSignatureDataEntry()
            self.signature_list_size += self.signature_header_size

    def AddSignatureData(self, SigDataObject):
        """Adds the Signature Data.

        Raises:
            (Exception): Signature size does not match Sig Data Object size
        """
        if (self.signature_size == 0):
            raise Exception(
                "Before adding Signature Data you must have set the Signature Size")

        if (self.signature_size != SigDataObject.get_total_size()):
            raise Exception("Can't add Signature Data of different size")

        if (self.signature_data_list is None):
            self.signature_data_list = []

        self.signature_data_list.append(SigDataObject)
        self.signature_list_size += self.signature_size

    def MergeSignatureList(self, esl):
        """Add the EfiSignatureData entries within the supplied EfiSignatureList to the current object.

        No sorting or deduplication is performed, the EfiSignatureData elements are simply appended
        """
        if not isinstance(esl, EfiSignatureList):
            raise Exception(
                "Parameter 1 'esl' must be of type EfiSignatureList")

        if (self.signature_type != esl.signature_type):
            raise Exception("Signature Types must match")

        if (self.signature_header_size > 0
           or esl.signature_header_size > 0):
            raise Exception("Merge does not support Signature Headers")
        self.signature_header_size = 0

        if (esl.signature_list_size == EfiSignatureList.STATIC_STRUCT_SIZE):
            # supplied EfiSignatureList is empty, return
            return

        FixedSizeData = esl.signature_data_list[0].FIXED_SIZE
        if not FixedSizeData:
            raise Exception(
                "Can only merge EfiSignatureLists with fixed-size data elements")

        if (self.signature_data_list is None):
            self.signature_data_list = []
            self.signature_size = esl.signature_size

        self.signature_data_list += esl.signature_data_list
        self.signature_list_size += esl.signature_list_size - \
            EfiSignatureList.STATIC_STRUCT_SIZE

    def SortBySignatureDataValue(self, deduplicate: bool = True):
        """Sort self's signature_data_list by signature_data values (ignores SigOwner) & optionally deduplicate.

        When deduplicate is true, remove duplicate signature_data values from self and return them in an
        EfiSignatureList.  This EfiSignatureList of duplicates is itself not deduplicated.

        When deduplicate is false, returns an empty EfiSignatureList (has 0 Data elements)
        """
        # initialize the duplicate list, an EFI_SIGNATURE_LIST with no signature data entries
        dupes = EfiSignatureList(typeguid=self.signature_type)
        dupes.signature_list_size = EfiSignatureList.STATIC_STRUCT_SIZE
        dupes.signature_header_size = self.signature_header_size
        dupes.signature_header = self.signature_header
        dupes.signature_size = 0
        dupes.signature_data_list = []

        # if nothing to sort, return the empty dupe list
        if (self.signature_data_list is None
           or len(self.signature_data_list) == 1):
            return dupes

        self.signature_data_list.sort(key=attrgetter('signature_data'))

        if (deduplicate is False):
            return dupes  # return empty dupe list without performing deduplicate

        # perform deduplicate on self
        last = len(self.signature_data_list) - 1  # index of the last item
        for i in range(last - 1, -1, -1):
            if self.signature_data_list[last].signature_data == self.signature_data_list[i].signature_data:
                dupes.signature_data_list.insert(
                    0, self.signature_data_list[last])
                dupes.signature_list_size += self.signature_size
                del self.signature_data_list[last]
                self.signature_list_size -= self.signature_size
                last = i
            else:
                last = i

        # only initialize dupes.signature_size if duplicate elements are present
        if (len(dupes.signature_data_list) > 0):
            dupes.signature_size = self.signature_size

        return dupes


class EfiSignatureDatabase(CommonUefiStructure):
    """Concatenation of EFI_SIGNATURE_LISTs, as is returned from UEFI GetVariable() on PK, KEK, db, & dbx.

    Useful for parsing and building the contents of the Secure Boot variables
    """

    def __init__(self, filestream: BinaryIO = None, EslList: List[EfiSignatureList] = None):
        """Inits an Efi Signature Database object.

        Args:
            filestream (:obj:`BinaryIO`, optional): Inits the object with this stream
            EslList (:obj:`list[EfiSignatureList]`, optional): Inits the object with this list
        """
        if filestream:
            self.EslList = []
            self.PopulateFromFileStream(filestream)
        else:
            self.EslList = [] if EslList is None else EslList

    def decode(self, fs: BinaryIO, decodesize: int = -1):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from
            decodesize (int, optional): Size to decode (UNUSED)

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
        """
        if (fs is None):
            raise Exception("Invalid File Stream")
        self.EslList = []
        begin = fs.tell()
        fs.seek(0, io.SEEK_END)
        end = fs.tell()  # end is offset after last byte
        fs.seek(begin)
        while (fs.tell() != end):
            Esl = EfiSignatureList(fs)
            self.EslList.append(Esl)

    def PopulateFromFileStream(self, fs: BinaryIO):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
        """
        return self.decode(fs)

    def print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        for Esl in self.EslList:
            Esl.print(compact=compact, outfs=outfs)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated, use print() instead.", DeprecationWarning, 2)
        self.print(compact=compact, outfs=outfs)

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
        """
        warn("Write() is deprecated, use write() instead.", DeprecationWarning, 2)
        self.write(fs)

    def write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        for Esl in self.EslList:
            Esl.write(fs)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        warn("GetBytes() is deprecated, use encode() instead.")
        return self.encode()

    def encode(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.write(fs)
            return fs.getvalue()

    def get_canonical_and_dupes(self):
        """Compute and return a tuple containing both a canonicalized database & a database of duplicates.

        Returns:
            (Tuple[EfiSignatureDatabase, EfiSignatureDatabase]): (canonical, duplicates)

        !!! note
            canonical is an EfiSignatureDatabase where EfiSignatureLists are merged (where possible),
                deduplicated, & sorted, and the EfiSignatureData elements are also deduplicated & sorted
            duplicates is an EfiSignatureDatabase with EfiSignatureLists containing any duplicated
                EfiSignatureData entries (only the data contents are checked for effective equality,
                signature owner is ignored)
        """
        # First group EFI_SIGNATURE_LISTS by type, merging them where possible

        sha256esl = None
        x509eslList = None

        for Esl in self.EslList:
            if (Esl.signature_data_list is None):  # discard empty EfiSignatureLists
                continue
            if (Esl.signature_type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
                if (sha256esl is None):
                    sha256esl = Esl  # initialize it
                else:
                    sha256esl.MergeSignatureList(Esl)
            elif (Esl.signature_type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
                if (x509eslList is None):
                    x509eslList = [Esl]  # initialize it
                else:
                    x509eslList.append(Esl)
            else:
                raise Exception("Unsupported signature type %s",
                                Esl.signature_type)

        # for each type, sort and de-duplicate, and then populate the respective databases
        # note the ordering of this section is the prescribed canonical order
        # first 1 EfiSignatureList for SHA256 hashes, EfiSignatureData elements sorted ascending
        # followed by EfiSignatureLists for each x509 certificate, sorted ascending by data content

        canonicalDb = EfiSignatureDatabase()
        duplicatesDb = EfiSignatureDatabase()

        if (sha256esl is not None):
            dupes = sha256esl.SortBySignatureDataValue(deduplicate=True)
            canonicalDb.EslList.append(sha256esl)
            duplicatesDb.EslList.append(dupes)

        if (x509eslList is not None):
            x509eslList.sort(key=attrgetter('signature_data_list'))
            for esl in x509eslList:
                if not canonicalDb.EslList:
                    canonicalDb.EslList.append(esl)
                elif esl == canonicalDb.EslList[-1]:
                    duplicatesDb.EslList.append(esl)
                else:
                    canonicalDb.EslList.append(esl)

        return (canonicalDb, duplicatesDb)

    def GetCanonicalAndDupes(self):
        """Compute and return a tuple containing both a canonicalized database & a database of duplicates.

        Returns:
            (Tuple[EfiSignatureDatabase, EfiSignatureDatabase]): (canonical, duplicates)

        !!! note
        canonical is an EfiSignatureDatabase where EfiSignatureLists are merged (where possible),
            deduplicated, & sorted, and the EfiSignatureData elements are also deduplicated & sorted
        duplicates is an EfiSignatureDatabase with EfiSignatureLists containing any duplicated
            EfiSignatureData entries (only the data contents are checked for effective equality,
            signature owner is ignored)
        """
        warn("GetCanonicalAndDupes() is deprecated. Use get_canonical_and_dupes() instead.", DeprecationWarning, 2)
        return self.get_canonical_and_dupes()

    def get_canonical(self):
        """Return a canonicalized EfiSignatureDatabase, see GetCanonicalAndDupes() for more details."""
        canonical, _ = self.get_canonical_and_dupes()
        return canonical

    def GetCanonical(self):
        """Return a canonicalized EfiSignatureDatabase, see GetCanonicalAndDupes() for more details."""
        warn("GetCanonical() is deprecated. Use get_canonical() instead.", DeprecationWarning, 2)
        return self.get_canonical()

    def get_duplicates(self):
        """Return an EfiSignatureDatabase of duplicates, see GetCanonicalAndDupes() for more details."""
        _, dupes = self.get_canonical_and_dupes()
        return dupes

    def GetDuplicates(self):
        """Return an EfiSignatureDatabase of duplicates, see GetCanonicalAndDupes() for more details."""
        warn("GetDuplicates() is deprecated. Use get_duplicates() instead.", DeprecationWarning, 2)
        return self.get_duplicates()


class EfiTime(CommonUefiStructure):
    """Object representing an EFI_TIME."""
    _StructFormat = '<H6BLh2B'
    _StructSize = struct.calcsize(_StructFormat)

    def __init__(self, time=datetime.datetime.now(), decodefs=None):
        """Inits an EFI_TIME object.

        Args:
            time (:obj:`datetime`, optional): Inits object with specified date (if decodefs not set)
            decodefs (:obj:`BinaryIO`, optional): Inits the object with this stream
        """
        if decodefs is None:
            self.time = time
        else:
            self.decode(decodefs)

    def decode(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (ValueError): Invalid filestream
            (ValueError): Invalid filestream size
        """
        if fs is None:
            raise ValueError("Invalid File Stream")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if (end - start) < EfiTime._StructSize:  # size of the static structure data
            raise ValueError("Invalid file stream size")
        (
            year,
            month,
            day,
            hour,
            minute,
            second,
            _,  # Pad1
            nano_second,
            time_zone,
            day_light,
            _   # Pad2
        ) = struct.unpack(EfiTime._StructFormat, fs.read(EfiTime._StructSize))

        self.time = datetime.datetime(
            year, month, day, hour, minute, second, nano_second // 1000)
        logging.debug("Timezone value is: 0x%x" % time_zone)
        logging.debug("Daylight value is: 0x%X" % day_light)

        return self.time

    def PopulateFromFileStream(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
        """
        warn("PopulateFromFileStream() is deprecated, use decode() instead", DeprecationWarning, 2)
        return self.decode(fs)

    def Print(self, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated, use print() instead", DeprecationWarning, 2)
        return self.print(outfs)

    def print(self, outfs=sys.stdout):
        """Prints to the console."""
        outfs.write("\nEfiTime: %s\n" % datetime.datetime.strftime(
            self.time, "%A, %B %d, %Y %I:%M%p"))

    def Encode(self):
        """Return's time as a packed EfiTime Structure."""
        warn("Encode() is deprecated use encode() instead", DeprecationWarning, 2)
        return self.encode()

    def encode(self):
        """Get's time as packed EfiTime structure."""
        return struct.pack(
            EfiTime._StructFormat,
            self.time.year,
            self.time.month,
            self.time.day,
            self.time.hour,
            self.time.minute,
            self.time.second,
            0,  # Pad1
            0,  # Nano Seconds
            0,  # Daylight
            0,  # TimeZone
            0   # Pad2
        )

    def write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (ValueError): Invalid filestream
        """
        if fs is None:
            raise ValueError("Invalid File Output Stream")

        fs.write(self.encode())

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (ValueError): Invalid filestream
        """
        warn("Write is deprecated(), use write() instead", DeprecationWarning, 2)
        self.write(fs)

    def __str__(self):
        """String representation of EFI_TIME."""
        return datetime.datetime.strftime(self.time, "%A, %B %d, %Y %I:%M%p")


class EfiVariableAuthentication2(CommonUefiStructure):
    """An object representing a EFI_VARIABLE_AUTHENTICATION_2."""

    def __init__(self, time=datetime.datetime.now(), decodefs=None):
        """Inits an EFI_VARIABLE_AUTHENTICATION_2 object.

        Args:
            time (:obj:`datetime`, optional): Inits object with specified date (if decodefs not set)
            decodefs (:obj:`BinaryIO`, optional): Inits the object with this stream
        """
        if decodefs:
            self.decode(decodefs)
            return

        self.time = EfiTime(time=time)
        self.auth_info = WinCertUefiGuid()
        self.payload = None
        self.payload_size = 0

        # Most variables do not have a sig list
        self.sig_list_payload = None

    def encode(self):
        """Encodes a new variable into a binary representation.

        :return: buffer - binary representation of the variable
        """
        buffer = self.time.encode() + self.auth_info.encode()

        if self.payload:
            buffer += self.payload

        return buffer

    def Encode(self, outfs=None):
        """Encodes a new variable into a binary representation.

        Args:
            outfs (BinaryIO): [default: None] write's to a file stream if provided

        :return: buffer - binary representation of the variable
        """
        warn("Encode() is deprecated, use encode() instead", DeprecationWarning, 2)

        buffer = self.encode()
        if outfs:
            outfs.write(buffer)

        return buffer

    def decode(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Steam")
        self.time = EfiTime(decodefs=fs)
        self.auth_info = WinCert.factory(fs)
        self.payload = None
        self.sig_list_payload = None

        self.set_payload(fs)

    def PopulateFromFileStream(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (ValueError): Invalid filestream
        """
        warn("PopulateFromFileStream() is deprecated, use decode() instead.", DeprecationWarning, 2)
        self.decode(fs)

    def print(self, outfs=sys.stdout):
        """Prints to the console."""
        outfs.write("EfiVariableAuthentication2\n")
        self.time.print(outfs)
        self.auth_info.print(outfs)

        outfs.write("\n-------------------- VARIABLE PAYLOAD --------------------\n")
        if self.sig_list_payload is not None:
            self.sig_list_payload.Print()

        elif self.payload is not None:
            outfs.write("Raw Data: \n")
            sdl = self.payload.tolist()
            if (self.payload_size != len(sdl)):
                raise Exception("Invalid Payload Data Size vs Length of data")
            hexdump(sdl, outfs=outfs)

    def Print(self, outfs=sys.stdout):
        """Prints to the console."""
        warn("Print() is deprecated, use print() instead.", DeprecationWarning, 2)
        self.print(outfs=outfs)

    def write(self, fs) -> None:
        """Serializes the object and writes it to a filestream.

        Args:
            fs (BinaryIO): filestream to write to

        Raises:
            (ValueError): Invalid filestream
        """
        if fs is None:
            raise ValueError("Invalid File Output Stream")

        self.time.write(fs)
        self.auth_info.write(fs)
        if self.payload is not None:
            fs.write(self.payload)

    def Write(self, fs) -> None:
        """Serializes the object and writes it to a filestream.

        Args:
            fs (BinaryIO): filestream to write to

        Raises:
            (ValueError): Invalid filestream
        """
        return self.write(fs)

    def SetPayload(self, fs) -> None:
        """Decodes a filestream and generates the payload.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (ValueError): Invalid filestream
        """
        warn("SetPayload() is deprecated, use set_payload() instead.", DeprecationWarning, 2)
        self.set_payload(fs)

    def set_payload(self, fs) -> None:
        """Decodes a filestream and generates the payload.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (ValueError): Invalid filestream
        """
        if fs is None:
            raise ValueError("Invalid File Input Stream")

        # Find the payload size
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)
        self.payload_size = end - start
        if self.payload_size == 0:
            logging.debug(
                "No Payload for this EfiVariableAuthenticated2 Object")
            return

        # Variables with the GUID EFI_IMAGE_SECURITY_DATABASE_GUID are formatted
        # as EFI_SIGNATURE_LIST
        try:
            self.sig_list_payload = EfiSignatureList(fs)
        except Exception:
            # Do nothing - we attempted to parse it as a sig list and it failed
            logging.debug("SigList Payload not detected.")

        # reset the file pointer
        fs.seek(start)
        self.payload = memoryview(fs.read(self.payload_size))


class EfiVariableAuthentication2Builder(object):
    """Builds EfiVariableAuthentication2 variables."""

    def __init__(self, name, guid, attributes, payload=None, efi_time=datetime.datetime.now()):
        """Builds a EfiVariableAuthentication2 structure.

        Args:
            name (str): Name of the UEFI Variable
            guid (str): Guid of the namespace the UEFI variable belongs to
            attributes (int | str): Attributes of the UEFI variable
            payload (io.BytesIO | bytes): binary payload to be signed and used as the value
                of the variable
            efi_time (time.datetime): EFI time of the datetime object

        """
        self.signature = b""

        # the authenticated variable to be returned
        self.authenticated_variable = EfiVariableAuthentication2(time=efi_time)

        # Start setting up the builder
        self.signature_builder = pkcs7.PKCS7SignatureBuilder()

        efi_attributes = EfiVariableAttributes(attributes)

        # if it's a string, convert it to a uuid type
        if isinstance(guid, str):
            guid = uuid.UUID(guid)

        # if it's still not a uuid lets warn the caller
        if not isinstance(guid, uuid.UUID):
            raise ValueError(f"guid is not the correct type: {type(guid)}")

        # This is the digest being signed that all signer's must sign
        self.digest_without_payload = name.encode('utf_16_le') + \
            guid.bytes_le + efi_attributes.encode() + self.authenticated_variable.time.encode()

        # Allow a caller to swap out the payload
        self.digest = self.digest_without_payload

        self.update_payload(payload)

    def get_digest(self) -> bytes:
        """Returns the digest to be signed."""
        return self.digest

    def get_signature(self) -> bytes:
        """Returns the Signature of the digest (PKCS#7 ContentInfo or SignedData structure)."""
        return self.signature

    def update_payload(self, payload) -> None:
        """Updates the authenticated variables payload and ultimately the digest.

        Args:
            payload (io.ByteIO | bytes): byte array or byte file stream of variable data

        Returns:
            None
        """
        # if provided with a payload, the serialized payload must be added to the Digest to be signed
        if not payload:
            logging.info("Empty payload")
            return

        # convert the payload to a file stream for SetPayload
        if not hasattr(payload, 'seek'):
            payload = io.BytesIO(payload)

        # Get the starting position and the length
        start = payload.tell()

        self.digest = self.digest_without_payload + payload.read()

        # before we pass it to SetPayload lets make sure we put the position back
        payload.seek(start)

        self.authenticated_variable.set_payload(payload)

    def sign(self, signing_certificate: Certificate, signing_private_key: RSAPrivateKey,
             additional_certificates: List = [], **kwargs) -> None:
        """Signs an authenticated variable.

        Args:
            signing_certificate (Certificate): x.509 format public key
            signing_private_key (RSAPrivateKey): x.509 format private key
            additional_certificates (list): list of x.509 format public keys to include
            **kwargs (Keyword Arguments): see Keyword Arguments

        Keyword Arguments:
            hash_algorithm (cryptography.hazmat.primitives.hashes): accepts cryptography.hazmat.primitives.hashes types
                to specify the hash_algorithm
            omit_content_info (bool): enabled by default, allows to include the content info asn.1 structure

        Returns:
            None
        """
        hash_algorithm = kwargs.get("hash_algorithm", SHA256())
        digest = kwargs.get("digest", self.digest)
        indent = kwargs.get("indent", " " * 4)

        # Set up the databuffer that will be signed
        self.signature_builder = self.signature_builder.set_data(digest)

        logging.info("")
        logging.info("Signing with Certificate: ")
        logging.info("%sIssuer: %s", indent, signing_certificate.issuer)
        logging.info("%sSubject: %s", indent, signing_certificate.subject)

        self.signature_builder = self.signature_builder.add_signer(
            signing_certificate, signing_private_key, hash_algorithm)

        for i, cert in enumerate(additional_certificates):
            indents = indent * i
            logging.info("")
            logging.info("%sAdding Additional Certificate: ", indents)
            logging.info("%sIssuer: %s", indents, cert.certificate.issuer)
            logging.info("%sSubject: %s", indents, cert.certificate.subject)

            # Add the certificate for verification
            self.signature_builder = self.signature_builder.add_certificate(cert.certificate)

    def finalize(self, omit_content_info=True) -> EfiVariableAuthentication2:
        """Finalizes the signature and returns a EfiVariableAuthentication2.

        Args:
            omit_content_info (bool): omits the asn.1 content info structure
                By specification this should be supported (and the SignedData structure) but this
                has been broken in tianocore for some time now

        Returns:
            EfiVariableAuthentication2
        """
        # Set the options for the pkcs7 signature:
        #   - The signature is detached
        #   - Do not convert LF to CRLF in the file (windows format)
        #   - Remove the attributes section from the pkcs7 structure
        options = [pkcs7.PKCS7Options.DetachedSignature,
                   pkcs7.PKCS7Options.Binary, pkcs7.PKCS7Options.NoAttributes]

        # The signature is enclosed in a asn1 content info structure
        self.signature = self.signature_builder.sign(Encoding.DER, options)

        # Up until recently including the content info section (on tianocore edk2 based implementations)
        # will cause UEFI to return `SECURITY_VIOLATION``
        if omit_content_info:
            content_info, _ = der_decode(
                self.signature, asn1Spec=rfc2315.ContentInfo())

            content_type = content_info.getComponentByName('contentType')
            if content_type != rfc2315.signedData:
                raise ValueError("This wasn't a signed data structure?")

            # Remove the contentInfo section and just return the sign data
            signed_data, _ = der_decode(content_info.getComponentByName(
                'content'), asn1Spec=rfc2315.SignedData())

            self.signature = der_encode(signed_data)

        self.authenticated_variable.auth_info.add_cert_data(self.signature)

        return self.authenticated_variable


class EFiVariableAuthentication2(EfiVariableAuthentication2):
    """An object representing a EFI_VARIABLE_AUTHENTICATION_2. DEPRECATED."""
    def __init__(self, time=datetime.datetime.now(), decodefs=None):
        """DEPRECATED. Use EfiVariableAuthentication2() instead. Initializes a EFiVariableAuthentication2."""
        warn("EFiVariableAuthentication2() is deprecated, use EfiVariableAuthentication2() instead.", DeprecationWarning, 2)  # noqa: E501
        super().__init__(time, decodefs=decodefs)


'''
THESE ARE NOT SUPPORTED IN THE TOOL

```
typedef struct {
  ///
  /// The SHA256 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA256_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA256;
```

```
typedef struct {
  ///
  /// The SHA384 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA384_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA384;
```

```
typedef struct {
  ///
  /// The SHA512 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA512_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA512;
```
'''
