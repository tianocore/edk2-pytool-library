# @file whea_parser.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier(self): BSD-2-Clause-Patent
##

import struct

"""
WHEA: Windows Hardware Error Architecture

TODO: Fill this out with breakdown of whea header
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

class WHEA_HEAD(object):

    STRUCT_FORMAT = "="
    placeholder = 0
    def __init__(self,whea_byte_array):
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
            self.Reserved) = struct.unpack_from(self.STRUCT_FORMAT, whea_byte_array)

    ##
    #
    ##
    def Revision_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Phase_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Reserved_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Error_Severity_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Payload_Size_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Additional_Info_1_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Additional_Info_2_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Module_ID_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Library_ID_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def Ihv_Sharing_Guid_Parse(self):
        return self.placeholder

    ##
    #
    ##
    def WHEA_Parse(self):
        return self.placeholder
