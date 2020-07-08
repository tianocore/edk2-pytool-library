# @file cper_head_parser.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct

#TODO Add more info here
"""
CPER: Common Platform Error Record

Structure of a CPER:
Signature         (4  bytes)  : CPER Signature
Revision          (4  bytes)  : The Revision of CPER
Signature End     (4  bytes)  : Must always be 0xffffffff
Section Count     (4  bytes)  : The Number of Sections of CPER
Error Severity    (4  bytes)  : The Severity of Error of CPER
Validation Bits   (4  bytes)  : Identify Valid IDs of the CPER
Record Length     (4  bytes)  : The size (in bytes) of the ENTIRE Error Record
Timestamp         (8  bytes)  : The Time at which the Error occured
Platform ID       (16 bytes)  : The Platform GUID (Typically, the Platform SMBIOS UUID)
Partition ID      (16 bytes)  : The Software Partition (if applicable)
Creator ID        (16 bytes)  : The GUID of the Error "Creator"
Notification Type (16 bytes)  : A pre-assigned GUID associated with the event (ex. Boot)
Record ID         (8  bytes)  : When combined with the Creator ID, identifies the Error Record
Flags             (4  bytes)  : A specific "flag" for the Error Record. Flags are pre-defined 
                                values which provide more information on the Error
Persistence Info  (8  bytes)  : Produced and consumed by the creator of the Error Record. There 
                                are no guidelines for these bytes.
Reserved          (12 bytes)  : Must be zero
"""

class CPER_HEAD(object):

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, cper_head_byte_array):
        (self.SignatureStart,
            self.Revision,
            self.SignatureEnd,
            self.SectionCount,
            self.ErrorSeverity,
            self.ValidationBytes,
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


    ##
    #
    ##
    def Signature_Parse(self,x):
        return x

    ##
    #
    ##
    def Revision_Parse(self,x):
        return x

    ##
    #
    ##
    def Section_Count_Parse(self,x):
        return x

    ##
    #
    ##
    def Error_Severity_Parse(self,x):
        return x

    ##
    #
    ##
    def Validation_Bytes_Parse(self,x):
        return x

    ##
    #
    ##
    def Record_Length_Parse(self,x):
        return x

    ##
    #
    ##
    def Timestamp_Parse(self,x):
        return x

    ##
    #
    ##
    def Platform_ID_Parse(self,x):
        return x

    ##
    #
    ##
    def Partition_ID_Parse(self,x):
        return x

    ##
    #
    ##
    def Creator_ID_Parse(self,x):
        return x

    ##
    #
    ##
    def Notification_Type_Parse(self,x):
        return x

    ##
    #
    ##
    def Record_ID_Parse(self,x):
        return x

    ##
    #
    ##
    def Flags_Parse(self,x):
        return x

    ##
    #
    ##
    def Persistence_Info_Parse(self,x):
        return x

    ##
    #
    ##
    def Reserved_Parse(self,x):
        return x
        
if __name__ == "__main__":
    CPER_Head_Parse(1)