##
# UEFI Authenticated Variable Structure Support Library
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import logging
import datetime
import struct
import hashlib
import uuid
import io
from typing import BinaryIO
from operator import attrgetter
from edk2toollib.uefi.wincert import WinCert, WinCertUefiGuid
from edk2toollib.utility_functions import PrintByteList

# spell-checker: ignore decodefs, createfs, deduplicated, deduplication

'''
Structures definition based on UEFI specification (UEFI 2.7)

Each object can be created and or populated from a file stream.
Each object can be written to a filesteam as binary and printed to the console in text.
'''

# UEFI global Variable Namespace
EfiGlobalVarNamespaceUuid = uuid.UUID('8BE4DF61-93CA-11d2-AA0D-00E098032B8C')
Sha256Oid = [0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01]

#
# EFI_SIGNATURE_DATA Structure for X509 Certs
#


class EfiSignatureDataEfiCertX509(object):
    STATIC_STRUCT_SIZE = 16
    FIXED_SIZE = False

    #
    # decodefs is a filestream object of binary content that is the structure encoded
    # decodesize is number of bytes to decode as the EFI_SIGNATURE_DATA object (guid + x509 data)
    # createfs is a filestream object that is the DER encoded x509 cert
    # cert is a bytes object containing the x509 certificate to initialize this object
    # sigowner is the uuid object of the signature owner guid
    def __init__(self,
                 decodefs: BinaryIO = None,
                 decodesize=0,
                 createfs: BinaryIO = None,
                 cert: bytes = None,
                 sigowner: uuid = None):
        if(decodefs is not None):
            self.PopulateFromFileStream(decodefs, decodesize)
        elif(createfs is not None):
            # create a new one
            self.SignatureOwner = sigowner
            start = createfs.tell()  # should be 0 but maybe this filestream has other things at the head
            createfs.seek(0, 2)
            end = createfs.tell()
            createfs.seek(start)
            self.SignatureDataSize = end - start
            if(self.SignatureDataSize < 0):
                raise Exception("Create File Stream has invalid size")
            self.SignatureData = (createfs.read(self.SignatureDataSize))
        elif(cert is not None):
            self.SignatureOwner = sigowner
            self.SignatureDataSize = len(cert)
            self.SignatureData = cert

        else:
            raise Exception("Invalid Parameters - Not Supported")

    def __lt__(self, other):
        """Less-than comparison for sorting. Looks at SignatureData only, not SignatureOwner"""
        return self.SignatureData < other.SignatureData

    def PopulateFromFileStream(self, fs: BinaryIO, decodesize):
        if(fs is None):
            raise Exception("Invalid File Steam")

        if(decodesize == 0):
            raise Exception("Invalid Decode Size")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if((end - offset) < EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE):  # size of the  guid
            raise Exception("Invalid file stream size")

        if((end - offset) < decodesize):  # size requested is too big
            raise Exception("Invalid file stream size vs decodesize")

        self.SignatureOwner = uuid.UUID(bytes_le=fs.read(16))

        # read remaining decode size for x509 data
        self.SignatureDataSize = decodesize - EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE
        self.SignatureData = fs.read(self.SignatureDataSize)

    def Print(self, compact: bool = False):
        if not compact:
            print("EfiSignatureData - EfiSignatureDataEfiCertX509")
            print("  Signature Owner:      %s" % str(self.SignatureOwner))
            print("  Signature Data: ")
            if(self.SignatureData is None):
                print("    NONE")
            else:
                sdl = self.SignatureData
                if(self.SignatureDataSize != len(sdl)):
                    raise Exception("Invalid Signature Data Size vs Length of data")
                PrintByteList(sdl)
        else:
            s = "ESD:EFI_CERT_X509,"
            s += "%s," % str(self.SignatureOwner)
            if(self.SignatureData is None):
                s += 'NONE'
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    s += '%02X' % sdl[index]
            print(s)

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")
        if(self.SignatureData is None):
            raise Exception("Invalid object")

        fs.write(self.SignatureOwner.bytes_le)
        fs.write(self.SignatureData)

    def GetBytes(self) -> bytes:
        """ Return bytes array produced by Write() """
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetTotalSize(self):
        return EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE + self.SignatureDataSize


#
# EFI_SIGNATURE_DATA Structure for Sha256 hash
#
class EfiSignatureDataEfiCertSha256(object):
    STATIC_STRUCT_SIZE = 16 + hashlib.sha256().digest_size  # has guid and array
    FIXED_SIZE = True

    #
    # decodefs is a filestream object of binary content that is the structure encoded
    # createfs is a filestream object of binary that is to be hashed to create the signature data
    # digest is a bytes object that contains the hash value for new signature data
    # sigowner is the uuid object of the signature owner guid
    def __init__(self,
                 decodefs: BinaryIO = None,
                 createfs: BinaryIO = None,
                 digest: bytes = None,
                 sigowner: uuid = None):
        if(decodefs is not None):
            self.PopulateFromFileStream(decodefs)
        elif(createfs is not None):
            # create a new one
            self.SignatureOwner = sigowner
            self.SignatureData = (hashlib.sha256(createfs.read()).digest())
        elif(digest is not None):
            digest_length = len(digest)
            if(digest_length != hashlib.sha256().digest_size):
                raise Exception("Invalid digest length (found / expected): (%d / %d)",
                                digest_length, hashlib.sha256().digest_size)
            self.SignatureOwner = sigowner
            self.SignatureData = digest
        else:
            raise Exception("Invalid Parameters - Not Supported")

    def PopulateFromFileStream(self, fs):
        if(fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if((end - offset) < EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE):  # size of the  data
            raise Exception("Invalid file stream size")

        self.SignatureOwner = uuid.UUID(bytes_le=fs.read(16))

        self.SignatureData = fs.read(hashlib.sha256().digest_size)

    def Print(self, compact: bool = False):
        if not compact:
            print("EfiSignatureData - EfiSignatureDataEfiCertSha256")
            print("  Signature Owner:      %s" % str(self.SignatureOwner))
            print("  Signature Data: ", end="")
            if(self.SignatureData is None):
                print(" NONE")
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    print("%02X" % sdl[index], end='')
                print("")
        else:
            s = 'ESD:EFI_CERT_SHA256,'
            s += "%s," % str(self.SignatureOwner)
            if(self.SignatureData is None):
                s += 'NONE'
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    s += '%02X' % sdl[index]
            print(s)

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")
        if(self.SignatureData is None):
            raise Exception("Invalid object")

        fs.write(self.SignatureOwner.bytes_le)
        fs.write(self.SignatureData)

    def GetBytes(self) -> bytes:
        """ Return bytes array produced by Write() """
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetTotalSize(self):
        return EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE


class EfiSignatureHeader(object):
    def __init__(self):
        raise Exception("Not Implemented")


class EfiSignatureDataFactory(object):
    EFI_CERT_SHA256_GUID = uuid.UUID('c1c41626-504c-4092-aca9-41f936934328')
    # EFI_CERT_RSA2048_GUID = uuid.UUID("0x3c5766e8, 0x269c, 0x4e34, 0xaa, 0x14, 0xed, 0x77, 0x6e, 0x85, 0xb3, 0xb6")
    # EFI_CERT_RSA2048_SHA256_GUID = uuid.UUID("0xe2b36190, 0x879b, 0x4a3d, 0xad, 0x8d, 0xf2, 0xe7, 0xbb, 0xa3, 0x27, 0x84")  # noqa: E501
    # EFI_CERT_SHA1_GUID = uuid.UUID("0x826ca512, 0xcf10, 0x4ac9, 0xb1, 0x87, 0xbe, 0x1, 0x49, 0x66, 0x31, 0xbd")
    # EFI_CERT_RSA2048_SHA1_GUID = uuid.UUID("0x67f8444f, 0x8743, 0x48f1, 0xa3, 0x28, 0x1e, 0xaa, 0xb8, 0x73, 0x60, 0x80")    # noqa: E501
    EFI_CERT_X509_GUID = uuid.UUID("a5c059a1-94e4-4aa7-87b5-ab155c2bf072")
    # EFI_CERT_SHA224_GUID = uuid.UUID("0xb6e5233, 0xa65c, 0x44c9, 0x94, 0x7, 0xd9, 0xab, 0x83, 0xbf, 0xc8, 0xbd")
    # EFI_CERT_SHA384_GUID = uuid.UUID("0xff3e5307, 0x9fd0, 0x48c9, 0x85, 0xf1, 0x8a, 0xd5, 0x6c, 0x70, 0x1e, 0x1")
    # EFI_CERT_SHA512_GUID = uuid.UUID("0x93e0fae, 0xa6c4, 0x4f50, 0x9f, 0x1b, 0xd4, 0x1e, 0x2b, 0x89, 0xc1, 0x9a")
    EFI_CERT_X509_SHA256_GUID = uuid.UUID("3bd2a492-96c0-4079-b420-fcf98ef103ed")
    # EFI_CERT_X509_SHA384_GUID = uuid.UUID("0x7076876e, 0x80c2, 0x4ee6, 0xaa, 0xd2, 0x28, 0xb3, 0x49, 0xa6, 0x86, 0x5b")     # noqa: E501
    # EFI_CERT_X509_SHA512_GUID = uuid.UUID("0x446dbf63, 0x2502, 0x4cda, 0xbc, 0xfa, 0x24, 0x65, 0xd2, 0xb0, 0xfe, 0x9d")     # noqa: E501
    # EFI_CERT_TYPE_PKCS7_GUID = uuid.UUID("0x4aafd29d, 0x68df, 0x49ee, 0x8a, 0xa9, 0x34, 0x7d, 0x37, 0x56, 0x65, 0xa7")

    #
    # This method is a factory for creating the correct Efi Signature Data object
    # from the filestream of an existing auth payload
    #
    @staticmethod
    def Factory(fs: BinaryIO, type, size):
        if(fs is None):
            raise Exception("Invalid File stream")

        if(type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            if(size != EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE):
                raise Exception("Invalid Size 0x%x" % size)
            return EfiSignatureDataEfiCertSha256(decodefs=fs)

        elif(type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(decodefs=fs, decodesize=size)

        else:
            logging.error("GuidType Value: %s" % type)
            raise Exception("Not Supported")
            return None

    #
    # Create a new Efi Signature Data object.
    #   Type will be baed on GUID
    #   Value will be based on type and Content (content stream opened for reading)
    #   sigowner is the UUID object for the signature owner guid
    @staticmethod
    def Create(type, ContentFileStream, sigowner):
        if(ContentFileStream is None):
            raise Exception("Invalid Content File Stream")

        if(type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            return EfiSignatureDataEfiCertSha256(createfs=ContentFileStream, sigowner=sigowner)
        elif(type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(createfs=ContentFileStream, sigowner=sigowner)
        else:
            raise Exception("Not Supported")

##
# EFI_SIGNATURE_LIST structure
##


class EfiSignatureList(object):
    STATIC_STRUCT_SIZE = 16 + 4 + 4 + 4

    def __init__(self, filestream: BinaryIO = None, typeguid: uuid = None):
        if(filestream is None):

            # Type of the signature. GUID signature types are defined in below.
            self.SignatureType = typeguid

            # Total size of the signature list, including this header.
            self.SignatureListSize = EfiSignatureList.STATIC_STRUCT_SIZE

            # Size of the signature header which precedes the array of signatures.
            self.SignatureHeaderSize = -1

            # Size of each signature.
            self.SignatureSize = 0

            # Header before the array of signatures. The format of this header is specified by the SignatureType.
            self.SignatureHeader = None

            # An array of signatures. Each signature is SignatureSize bytes in length.
            self.SignatureData_List = None

        else:
            self.PopulateFromFileStream(filestream)

    def PopulateFromFileStream(self, fs: BinaryIO):
        if(fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if((end - start) < EfiSignatureList.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")

        self.SignatureType = uuid.UUID(bytes_le=fs.read(16))
        self.SignatureListSize = struct.unpack("<I", fs.read(4))[0]
        self.SignatureHeaderSize = struct.unpack("<I", fs.read(4))[0]
        self.SignatureSize = struct.unpack("<I", fs.read(4))[0]

        # check the total size of this is within the File
        if((end - start) < self.SignatureListSize):
            logging.debug("SignatureListSize 0x%x" % self.SignatureListSize)
            logging.debug("End - Start is 0x%x" % (end - start))
            raise Exception("Invalid File Stream.  Not enough file content to cover the Sig List Size")

        # check that structure is built correctly and there is room within the structure total size to read the header
        if((self.SignatureListSize - (fs.tell() - start)) < self.SignatureHeaderSize):
            raise Exception("Invalid Sig List.  Sizes not correct.  "
                            "SignatureHeaderSize extends beyond end of structure")

        # Signature Header is allowed to be nothing (size 0)
        self.SignatureHeader = None
        if(self.SignatureHeaderSize > 0):
            self.SignatureHeader = EfiSignatureHeader(fs, self.SignatureHeaderSize)

        if(((self.SignatureListSize - (fs.tell() - start)) % self.SignatureSize) != 0):
            raise Exception("Invalid Sig List.  Signature Data Array is not a valid size")

        self.SignatureData_List = []
        while((start + self.SignatureListSize) > fs.tell()):
            # double check that everything is adding up correctly.
            if((start + self.SignatureListSize - fs.tell() - self.SignatureSize) < 0):
                raise Exception("Invalid Signature List Processing.  Signature Data not correctly parsed!!")
            a = EfiSignatureDataFactory.Factory(fs, self.SignatureType, self.SignatureSize)
            self.SignatureData_List.append(a)

    def Print(self, compact: bool = False):
        if not compact:
            print("EfiSignatureList")
            print("  Signature Type:        %s" % str(self.SignatureType))
            print("  Signature List Size:   0x%x" % self.SignatureListSize)
            print("  Signature Header Size: 0x%x" % self.SignatureHeaderSize)
            print("  Signature Size:        0x%x" % self.SignatureSize)
            if(self.SignatureHeader is not None):
                self.SignatureHeader.Print(compact=compact)
            else:
                print("  Signature Header:      NONE")
        else:
            csv = "ESL:"
            csv += "%s" % str(self.SignatureType)
            csv += ",0x%x" % self.SignatureListSize
            csv += ",0x%x" % self.SignatureHeaderSize
            csv += ",0x%x" % self.SignatureSize
            if(self.SignatureHeader is not None):
                csv += self.SignatureHeader.Print(compact=compact)
            else:
                csv += ",NONE"
            print(csv)

        if(self.SignatureData_List is not None):
            for a in self.SignatureData_List:
                a.Print(compact=compact)

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")
        if((self.SignatureHeader is None) and (self.SignatureHeaderSize == -1)):
            raise Exception("Invalid object.  Uninitialized Sig Header")

        fs.write(self.SignatureType.bytes_le)
        fs.write(struct.pack("<I", self.SignatureListSize))
        fs.write(struct.pack("<I", self.SignatureHeaderSize))
        fs.write(struct.pack("<I", self.SignatureSize))
        if(self.SignatureHeader is not None):
            self.SignatureHeader.Write(fs)

        if(self.SignatureData_List is not None):
            for a in self.SignatureData_List:
                a.Write(fs)

    def GetBytes(self) -> bytes:
        """ Return bytes array produced by Write() """
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def AddSignatureHeader(self, SigHeader, SigSize=0):
        if(self.SignatureHeader is not None):
            raise Exception("Signature Header already set")

        if(self.SignatureHeaderSize != -1):
            raise Exception("Signature Header already set (size)")

        if(self.SignatureSize != 0):
            raise Exception("Signature Size already set")

        if(self.SignatureData_List is not None):
            raise Exception("Signature Data List is already initialized")

        self.SignatureHeader = SigHeader
        if(SigHeader is None):
            self.SignatureHeaderSize = 0
            self.SignatureSize = SigSize
        else:
            self.SignatureHeaderSize = SigHeader.GetTotalSize()
            self.SignatureSize = SigHeader.GetSizeOfSignatureDataEntry()
            self.SignatureListSize += self.SignatureHeaderSize

    def AddSignatureData(self, SigDataObject):
        if(self.SignatureSize == 0):
            raise Exception("Before adding Signature Data you must have set the Signature Size")

        if(self.SignatureSize != SigDataObject.GetTotalSize()):
            raise Exception("Can't add Signature Data of different size")

        if(self.SignatureData_List is None):
            self.SignatureData_List = []

        self.SignatureData_List.append(SigDataObject)
        self.SignatureListSize += self.SignatureSize

    def MergeSignatureList(self, esl):
        """
        Add the EfiSignatureData entries within the supplied EfiSignatureList to the current object

        No sorting or deduplication is performed, the EfiSignatureData elements are simply appended
        """

        if not isinstance(esl, EfiSignatureList):
            raise Exception("Parameter 1 'esl' must be of type EfiSignatureList")

        if(self.SignatureType != esl.SignatureType):
            raise Exception("Signature Types must match")

        if(self.SignatureHeaderSize > 0
           or esl.SignatureHeaderSize > 0):
            raise Exception("Merge does not support Signature Headers")
        self.SignatureHeaderSize = 0

        if(esl.SignatureListSize == EfiSignatureList.STATIC_STRUCT_SIZE):
            # supplied EfiSignatureList is empty, return
            return

        FixedSizeData = esl.SignatureData_List[0].FIXED_SIZE
        if not FixedSizeData:
            raise Exception("Can only merge EfiSignatureLists with fixed-size data elements")

        if(self.SignatureData_List is None):
            self.SignatureData_List = []
            self.SignatureSize = esl.SignatureSize

        self.SignatureData_List += esl.SignatureData_List
        self.SignatureListSize += esl.SignatureListSize - EfiSignatureList.STATIC_STRUCT_SIZE

    def SortBySignatureDataValue(self, deduplicate: bool = True):
        """
        Sort self's SignatureData_List by SignatureData values (ignores SigOwner) & optionally deduplicate

        When deduplicate is true, remove duplicate SignatureData values from self and return them in an
        EfiSignatureList.  This EfiSignatureList of duplicates is itself not deduplicated.

        When deduplicate is false, returns an empty EfiSignatureList (has 0 Data elements)
        """

        # initialize the duplicate list, an EFI_SIGNATURE_LIST with no signature data entries
        dupes = EfiSignatureList(typeguid=self.SignatureType)
        dupes.SignatureListSize = EfiSignatureList.STATIC_STRUCT_SIZE
        dupes.SignatureHeaderSize = self.SignatureHeaderSize
        dupes.SignatureHeader = self.SignatureHeader
        dupes.SignatureSize = 0
        dupes.SignatureData_List = []

        # if nothing to sort, return the empty dupe list
        if(self.SignatureData_List is None
           or len(self.SignatureData_List) == 1):
            return dupes

        self.SignatureData_List.sort(key=attrgetter('SignatureData'))

        if(deduplicate is False):
            return dupes  # return empty dupe list without performing deduplicate

        # perform deduplicate on self
        last = len(self.SignatureData_List) - 1  # index of the last item
        for i in range(last - 1, -1, -1):
            if self.SignatureData_List[last].SignatureData == self.SignatureData_List[i].SignatureData:
                dupes.SignatureData_List.insert(0, self.SignatureData_List[last])
                dupes.SignatureListSize += self.SignatureSize
                del self.SignatureData_List[last]
                self.SignatureListSize -= self.SignatureSize
                last = i
            else:
                last = i

        # only initialize dupes.SignatureSize if duplicate elements are present
        if(len(dupes.SignatureData_List) > 0):
            dupes.SignatureSize = self.SignatureSize

        return dupes


class EfiSignatureDatabase(object):
    """
    Concatenation of EFI_SIGNATURE_LISTs, as is returned from UEFI GetVariable() on PK, KEK, db, & dbx

    Useful for parsing and building the contents of the Secure Boot variables
    """

    def __init__(self, filestream: BinaryIO = None, EslList: [] = None):
        if filestream:
            self.EslList = []
            self.PopulateFromFileStream(filestream)
        else:
            self.EslList = [] if EslList is None else EslList

    def PopulateFromFileStream(self, fs: BinaryIO):
        if(fs is None):
            raise Exception("Invalid File Stream")
        self.EslList = []
        begin = fs.tell()
        fs.seek(0, io.SEEK_END)
        end = fs.tell()  # end is offset after last byte
        fs.seek(begin)
        while (fs.tell() != end):
            Esl = EfiSignatureList(fs)
            self.EslList.append(Esl)

    def Print(self, compact: bool = False):
        for Esl in self.EslList:
            Esl.Print(compact=compact)

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")
        for Esl in self.EslList:
            Esl.Write(fs)

    def GetBytes(self) -> bytes:
        """ Return bytes array produced by Write() """
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetCanonicalAndDupes(self):
        """
        Compute and return a tuple containing both a canonicalized database & a database of duplicates

        Returns -> (canonical: EfiSignatureDatabase, duplicates: EfiSignatureDatabase)
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
            if(Esl.SignatureData_List is None):  # discard empty EfiSignatureLists
                continue
            if(Esl.SignatureType == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
                if(sha256esl is None):
                    sha256esl = Esl  # initialize it
                else:
                    sha256esl.MergeSignatureList(Esl)
            elif(Esl.SignatureType == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
                if(x509eslList is None):
                    x509eslList = [Esl]  # initialize it
                else:
                    x509eslList.append(Esl)
            else:
                raise Exception("Unsupported signature type %s", Esl.SignatureType)

        # for each type, sort and de-duplicate, and then populate the respective databases
        # note the ordering of this section is the prescribed canonical order
        # first 1 EfiSignatureList for SHA256 hashes, EfiSignatureData elements sorted ascending
        # followed by EfiSignatureLists for each x509 certificate, sorted ascending by data content

        canonicalDb = EfiSignatureDatabase()
        duplicatesDb = EfiSignatureDatabase()

        if(sha256esl is not None):
            dupes = sha256esl.SortBySignatureDataValue(deduplicate=True)
            canonicalDb.EslList.append(sha256esl)
            duplicatesDb.EslList.append(dupes)

        if(x509eslList is not None):
            x509eslList.sort(key=attrgetter('SignatureData_List'))
            for esl in x509eslList:
                if not canonicalDb.EslList:
                    canonicalDb.EslList.append(esl)
                elif esl == canonicalDb.EslList[-1]:
                    duplicatesDb.EslList.append(esl)
                else:
                    canonicalDb.EslList.append(esl)

        return (canonicalDb, duplicatesDb)

    def GetCanonical(self):
        """Return a canonicalized EfiSignatureDatabase, see GetCanonicalAndDupes() for more details"""
        (canonical, dupes) = self.GetCanonicalAndDupes()
        return canonical

    def GetDuplicates(self):
        """Return an EfiSignatureDatabase of duplicates, see GetCanonicalAndDupes() for more details"""
        (canonical, dupes) = self.GetCanonicalAndDupes()
        return dupes


class EfiTime(object):
    STATIC_STRUCT_SIZE = 16

    def __init__(self, Time=datetime.datetime.now(), decodefs=None):

        if(decodefs is None):
            self.Time = Time
        else:
            self.PopulateFromFileStream(decodefs)

    def PopulateFromFileStream(self, fs):
        if(fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if((end - start) < EfiTime.STATIC_STRUCT_SIZE):  # size of the static structure data
            raise Exception("Invalid file stream size")

        Year = struct.unpack("<H", fs.read(2))[0]
        Month = struct.unpack("<B", fs.read(1))[0]
        Day = struct.unpack("<B", fs.read(1))[0]
        Hour = struct.unpack("<B", fs.read(1))[0]
        Minute = struct.unpack("<B", fs.read(1))[0]
        Second = struct.unpack("<B", fs.read(1))[0]
        fs.seek(1, 1)  # seek past pad1
        NanoSecond = struct.unpack("<I", fs.read(4))[0]
        TimeZone = struct.unpack("<h", fs.read(2))[0]
        Daylight = struct.unpack("<B", fs.read(1))[0]
        fs.seek(1, 1)  # seek past pad2

        self.Time = datetime.datetime(Year, Month, Day, Hour, Minute, Second, NanoSecond / 1000)
        logging.debug("I don't know how to deal with TimeZone or Daylight and I don't care at the moment")
        logging.debug("Timezone value is: 0x%x" % TimeZone)
        logging.debug("Daylight value is: 0x%X" % Daylight)

    def Print(self):
        print("EfiTime: %s" % datetime.datetime.strftime(self.Time, "%A, %B %d, %Y %I:%M%p"))

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")

        fs.write(struct.pack("<H", self.Time.year))
        fs.write(struct.pack("<B", self.Time.month))
        fs.write(struct.pack("<B", self.Time.day))
        fs.write(struct.pack("<B", self.Time.hour))
        fs.write(struct.pack("<B", self.Time.minute))
        fs.write(struct.pack("<B", self.Time.second))
        fs.write(struct.pack("<B", 0))  # Pad1
        fs.write(struct.pack("<I", 0))  # Nano Seconds
        fs.write(struct.pack("<h", 0))  # TimeZone
        fs.write(struct.pack("<B", 0))  # Daylight
        fs.write(struct.pack("<B", 0))  # Pad2


class EFiVariableAuthentication2(object):

    def __init__(self, Time=datetime.datetime.now(), decodefs=None):
        if(decodefs is None):
            self.EfiTime = EfiTime(Time=Time)
            self.AuthInfo = WinCertUefiGuid()
            self.Payload = None
            self.PayloadSize = 0
            self.SigListPayload = None
        else:
            self.PopulateFromFileStream(decodefs)

    def PopulateFromFileStream(self, fs):
        if(fs is None):
            raise Exception("Invalid File Steam")
        self.EfiTime = EfiTime(decodefs=fs)
        self.AuthInfo = WinCert.Factory(fs)
        self.Payload = None
        self.SigListPayload = None

        self.SetPayload(fs)

    def Print(self):
        print("EFiVariableAuthentication2")
        self.EfiTime.Print()
        self.AuthInfo.Print()
        print("-------------------- VARIABLE PAYLOAD --------------------")
        if(self.SigListPayload is not None):
            self.SigListPayload.Print()

        elif(self.Payload is not None):
            print("Raw Data: ")
            sdl = self.Payload.tolist()
            if(self.PayloadSize != len(sdl)):
                raise Exception("Invalid Payload Data Size vs Length of data")
            PrintByteList(sdl)

    def Write(self, fs):
        if(fs is None):
            raise Exception("Invalid File Output Stream")

        self.EfiTime.Write(fs)
        self.AuthInfo.Write(fs)
        if(self.Payload is not None):
            fs.write(self.Payload)

    def SetPayload(self, fs):
        if(fs is None):
            raise Exception("Invalid File Input Stream")

        # Find the payload size
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)
        self.PayloadSize = end - start
        if(self.PayloadSize == 0):
            logging.debug("No Payload for this EfiVariableAuthenticated2 Object")
            return

        # read as siglist
        try:
            self.SigListPayload = EfiSignatureList(fs)
        except Exception as e:
            logging.debug("Exception Trying to parse SigList Payload.  \n%s" % str(e))

        # reset the file pointer
        fs.seek(start)
        self.Payload = memoryview(fs.read(self.PayloadSize))


'''
THESE ARE NOT SUPPORTED IN THE TOOL

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
'''
