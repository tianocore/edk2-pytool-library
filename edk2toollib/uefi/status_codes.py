# @file
# Code to help convert an Int to StatusCode string
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


class UefiStatusCode(object):
    # See appendix D of the UEFI spec

    # high bit set
    ErrorCodeStrings = ["NOT VALID", "Load Error", "Invalid Parameter", "Unsupported", "Bad BufferSize",
                        "Buffer Too Small", "Not Ready", "Device Error", "Write Protected", "Out of Resources",
                        "Volume Corrupt", "Volume Full", "No Media", "Media Changed", "Not Found", "Access Denied",
                        "No Response", "No Mapping", "Time Out", "Not Started", "Already Started", "Aborted",
                        "ICMP Error", "TFTP Error", "Protocol Error", "Incompatible Error", "Security Violation",
                        "CRC Error", "End of Media", "Reserved(29)", "Reserved(30)", "End of File",
                        "Invalid Language", "Compromised Data", "IP Address Conflict", "HTTP Error"]

    NonErrorCodeStrings = ["Success", "Unknown Glyph", "Delete Failure", "Write Failure", "Buffer Too Small",
                           "Stale Data", "File System", "Reset Required"]

    def Convert32BitToString(self, i: int) -> str:
        ''' convert 632bit int to a friendly UEFI status code string value'''
        a = UefiStatusCode.NonErrorCodeStrings

        if (i >> 31) & 1 == 1:
            # error
            a = UefiStatusCode.ErrorCodeStrings
            i = i & 0x7FFFFFFF  # mask off upper bit

        if(i >= len(a)):
            return "Undefined StatusCode"

        return a[i]

    def Convert64BitToString(self, l: int) -> str:
        ''' convert 64bit int to a friendly UEFI status code string value'''
        a = UefiStatusCode.NonErrorCodeStrings

        if (l >> 63) & 1 == 1:
            # error
            a = UefiStatusCode.ErrorCodeStrings
            l = l & 0x7FFFFFFFFFFFFFFF  # mask off upper bit

        if(l >= len(a)):
            return "Undefined StatusCode"

        return a[l]

    def ConvertHexString64ToString(self, hexstring: str) -> str:
        ''' convert 64 bit hexstring in 0x format to a UEFI status code '''
        value = int(hexstring, 16)
        return self.Convert64BitToString(value)

    def ConvertHexString32ToString(self, hexstring):
        ''' convert 32 bit hexstring in 0x format to a UEFI status code '''
        value = int(hexstring, 16)
        return self.Convert32BitToString(value)
