# @file cperheadparser.py
# Parses the header of a CPER
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct
import uuid
import sys

"""
CPER: Common Platform Error Record

Structure of a CPER:
Signature           (0   byte offset, 4  byte length) : CPER Signature
Revision            (4   byte offset, 2  byte length) : Represents the major and minor version number of the Error Record definition
Signature End       (6   byte offset, 4  byte length) : Must always be 0xffffffff
Section Count       (10  byte offset, 4  byte length) : The Number of Sections of CPER
Error Severity      (12  byte offset, 4  byte length) : The Severity of Error of CPER
Validation Bits     (16  byte offset, 4  byte length) : Identify Valid IDs of the CPER
Record Length       (20  byte offset, 4  byte length) : The size(in bytes) of the ENTIRE Error Record
Timestamp           (24  byte offset, 8  byte length) : The Time at which the Error occured
Platform ID         (32  byte offset, 16 byte length) : The Platform GUID (Typically, the Platform SMBIOS UUID)
Partition ID        (48  byte offset, 16 byte length) : The Software Partition (if applicable)
Creator ID          (64  byte offset, 16 byte length) : The GUID of the Error "Creator"
Notification Type   (80  byte offset, 16 byte length) : A pre-assigned GUID associated with the event (ex.Boot)
Record ID           (96  byte offset, 8  byte length) : When combined with the Creator ID, identifies the Error Record
Flags               (104 byte offset, 4  byte length) : A specific "flag" for the Error Record. Flags are pre-defined values which provide more information on the Error
Persistence Info    (108 byte offset, 8  byte length) : Produced and consumed by the creator of the Error Record.There are no guidelines for these bytes.
Reserved            (116 byte offset, 12 byte length) : Must be zero
"""

"""
Python Struct Format Characters

Format      C Type                  Python Type     Standard Size
x           pad byte                none            1
c           char                    integer         1
b           signed char             integer         1
B           unsigned char           integer         1
?           _Bool                   bool            1
h           short                   integer         2
H           unsigned short          integer         2
i           int                     integer         4
I           unsigned int            integer         4
l           long                    integer         4
L           unsigned long           integer         4
q           long long               integer         8
Q           unsigned long long      integer         8
n           ssize_t                 integer
N           size_t                  integer
e           (6)                     float           2
f           float                   float           4
d           double                  float           8
s           char[]                  bytes
p           char[]                  bytes
P           void *                  integer
"""


class CPER_HEAD(object):

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, cper_head_byte_array):
        (self.SignatureStart,
         self.Revision,
         self.SignatureEnd,
         self.SectionCount,
         self.ErrorSeverity,
         self.ValidationBits,
         self.RecordLength,
         self.Timestamp,
         self.PlatformID,
         self.PartitionID,
         self.CreatorID,
         self.NotificationType,
         self.RecordID,
         self.Flags,
         self.PersistenceInfo,
         self.Reserved) = struct.unpack_from(self.STRUCT_FORMAT, cper_head_byte_array)
            
        self.FlagList = []
        self.ValidBitsList = [False,False,False]
        self.TimestampFriendly = ""

    ##
    # Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"
    ##
    def SignatureParse(self):
        return str(self.SignatureStart)

    ##
    # Parse the major and minor version number of the Error Record definition
    #
    # TODO: Actually parse out the zeroth and first byte which represent the minor and major version numbers respectively 
    ##
    def RevisionParse(self):
        return self.Revision

    ##
    #
    ##
    def ErrorSeverityParse(self):
        if(self.ErrorSeverity == 0):
            return "Recoverable"
        elif(self.ErrorSeverity == 1):
            return "Fatal"
        elif(self.ErrorSeverity == 2):
            return "Corrected"
        elif(self.ErrorSeverity == 3):
            return "Informational"
        
        return "Unknown"

    ##
    # if bit 1: PlatformID contains valid info
    # if bit 2: Timestamp contains valid info
    # if bit 3: PartitionID contains valid info
    ##
    def ValidationBitsParse(self):
        if(self.ValidationBits & int('0b1', 2)):
            self.ValidBitsList[0] = True
        if(self.ValidationBits & int('0b10', 2)):
            self.ValidBitsList[1] = True
        if(self.ValidationBits & int('0b100', 2)):
            self.ValidBitsList[2] = True

    ##
    # Convert the timestamp into a friendly version formatted to (MM/DD/YY Hours:Minutes:Seconds)
    ##
    def TimestampParse(self):
        if(self.ValidBitsList[1]):
            self.TimestampFriendly = str((self.Timestamp >> 5) & int('0b11111111', 2)) + "/" + \
                                     str((self.Timestamp >> 4) & int('0b11111111', 2)) + "/" + \
                                     str((self.Timestamp >> 6) & int('0b11111111', 2)) + " " + \
                                     str((self.Timestamp >> 2) & int('0b11111111', 2)) + ":" + \
                                     str((self.Timestamp >> 1) & int('0b11111111', 2)) + ":" + \
                                     str((self.Timestamp >> 0) & int('0b11111111', 2))

    ##
    # Parse the Platform GUID (Typically, the Platform SMBIOS UUID)
    ##
    def PlatformIDParse(self):
        
        if(self.ValidBitsList[0]):
            try:
                guid = uuid.UUID(bytes=self.PlatformID)
                return guid
            except:
                pass

        return uuid.UUID(bytes=bytes(16))

    ##
    # Parse the GUID for the Software Partition (if applicable)
    ##
    def PartitionIDParse(self):
        if(self.ValidBitsList[2]):
            try:
                guid = uuid.UUID(bytes=self.PartitionID)
                return guid
            except:
                pass
    
        return uuid.UUID(bytes=bytes(16))

    ##
    # Parse the GUID for the GUID of the Error "Creator"
    ##
    def CreatorIDParse(self):
        try:
            guid = uuid.UUID(bytes=self.CreatorID)
            return guid
        except:
            return uuid.UUID(bytes=bytes(16))

    ##
    # Parse the pre-assigned GUID associated with the event (ex.Boot)
    ##
    def NotificationTypeParse(self):
        try:
            guid = uuid.UUID(bytes=self.NotificationType)
            return guid
        except:
            return uuid.UUID(bytes=bytes(16))

    ##
    # When combined with the Creator ID, Record ID identifies the Error Record
    ##
    def RecordIDParse(self):
        return self.RecordID

    ##
    # Check the flags field and populate list containing applicable flags
    ##
    def FlagsParse(self):

        if(self.Flags & int('0b1', 2)):
            self.FlagList.append("Recovered")
        if(self.Flags & int('0b10', 2)):
            self.FlagList.append("Previous Error")
        if(self.Flags & int('0b100', 2)):
            self.FlagList.append("Simulated")
        if(self.Flags & int('0b1000', 2)):
            self.FlagList.append("Device Driver")
        if(self.Flags & int('0b10000', 2)):
            self.FlagList.append("Critical")
        if(self.Flags & int('0b100000', 2)):
            self.FlagList.append("Persist")

    ##
    # Parse the persistence info which is produced and consumed by the creator of the Error Record
    ##
    def PersistenceInfoParse(self):
        return self.PersistenceInfo
