# @file cper_head_parser.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

##
# CPER: Common Platform Error Record
##

##
# Mask for capturing bits
##

# Capture One Byte
OneByteMask = 2**9 - 1
# Capture Two Bytes
TwoByteMask = 2**17 - 1
# Capture Four Bytes
FourByteMask = 2**33 - 1 
# Capture Eight Bytes
EightByteMask = 2**65 - 1

##
# Offsets for each variable within a CPER
##

# Offset to bits which indicate CPER Signature
SignatureOffset = 0
# Offset to bits which indicate the Revision of CPER
RevisionOffset = 4
# Offset to bits which indicate the Number of Sections of CPER
SectionCountoffset = 10
# Offset to bits which indicate the Severity of Error of CPER
ErrorSeverityOffset = 12
# Offset to bits which identify Valid IDs of the CPER
ValidationBitsOffset = 16
# Offset to bits which indicate the size (in bytes) of the ENTIRE Error Record
RecordLengthOffset = 20
# Offset to bits which indicate the Time at which the Error occured
TimestampOffset = 24
# Offset to bits which indicate the Platform GUID (Typically, the Platform SMBIOS UUID)
PlatformIDOffset = 32
# Offset to bits which indicate the Software Partition (if applicable)
PartitionIDOffset = 48
# Offset to bits which indicate the GUID of the Error "Creator"
CreatorIDOffset = 64
# Offset to bits which contain a pre-assigned GUID associated with the event (ex. Boot)
NotificationTypeOffset = 80
# Offset to bits which, when combined with the Creator ID, identifies the Error Record
RecordIDOffset = 96
# Offset to bits which indicate a specific "flag" for the Error Record. Flags are pre-defined values which
# provide more information on the Error
FlagsOffset = 104
# Offset to bits which are produced and consumed by the creator of the Error Record. There are no
# guidelines for these bytes.
PersistenceInfoOffset = 108


##
#
##
def Signature_Parse(x):
    return x & FourByteMask

##
#
##
def Revision_Parse(x):
    return x & TwoByteMask

##
#
##
def Section_Count_Parse(x):
    return x & TwoByteMask

##
#
##
def Error_Severity_Parse(x):
    return x & FourByteMask

##
#
##
def Validation_bits_Parse(x):
    return x & FourByteMask

##
#
##
def Record_Length_Parse(x):
    return x & FourByteMask

##
#
##
def Timestamp_Parse(x):
    return x

##
#
##
def Platform_ID_Parse(x):
    return x

##
#
##
def Partition_ID_Parse(x):
    return x

##
#
##
def Creator_ID_Parse(x):
    return x

##
#
##
def Notification_Type_Parse(x):
    return x

##
#
##
def Record_ID_Parse(x):
    return x & EightByteMask

##
#
##
def Flags_Parse(x):
    return x & FourByteMask

##
#
##
def Persistence_Info_Parse(x):
    return x & EightByteMask

##
#
##
def Reserved_Parse(x):
    return x & OneByteMask

###
# Main Parser
###
def CPER_Head_Parse(x):
    print("Result: " + str(Signature_Parse(int('01011000101111010000010000110111000101001100001101101101',2))))
    return x

if __name__ == "__main__":
    CPER_Head_Parse(1)