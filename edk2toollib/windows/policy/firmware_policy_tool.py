# @file
# Generate the test firmware policy blobs for
# the Firmware Policy Parsing Library Unit Test
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

from edk2toollib.windows.policy.firmware_policy import FirmwarePolicy
import argparse


def PrintPolicy(filename):
    try:
        with open(filename, "rb") as f:
            policy = FirmwarePolicy(fs=f)
            policy.Print()

    except FileNotFoundError:
        print('ERROR:  File not found: "{0}"'.format(filename))


def CreatePolicyFromParameters(filename, manf, product, sn, nonce, oem1, oem2):
    with open(filename, "xb") as f:
        policy = FirmwarePolicy()
        TargetInfo = {'Manufacturer': manf,
                      'Product': product,
                      'SerialNumber': sn,
                      'OEM_01': oem1,
                      'OEM_02': oem2,
                      'Nonce': nonce}
        policy.SetDeviceTarget(TargetInfo)
        policy.Serialize(output=f)
        policy.Print()


def main():
    parser = argparse.ArgumentParser(description='Firmware Policy Tool')
    subparsers = parser.add_subparsers(required=True, dest='action')

    parser_create = subparsers.add_parser('create', help='Create a firmware policy')
    parser_create.add_argument('PolicyFilename', type=str, help='The name of the binary policy file to create')
    parser_create.add_argument(
        'Manufacturer', type=str, help='Manufacturer Name, for example, "Contoso Computers, LLC".  '
        'Should match the EV Certificate Subject CN="Manufacturer"')
    parser_create.add_argument('Product', type=str, help='Product Name, for example, "Laptop Foo"')
    parser_create.add_argument(
        'SerialNumber', type=str, help='Serial Number, for example "F0013-000243546-X02".  Should match '
        'SmbiosSystemSerialNumber, SMBIOS System Information (Type 1 Table) -> Serial Number')
    parser_create.add_argument('NonceHex', type=str, help='The nonce in hexadecimal, for example "0x0123456789abcdef"')
    parser_create.add_argument('--OEM1', type=str, default='',
                               help='Optional OEM Field 1, an arbitrary length string, for example "ODM foo"')
    parser_create.add_argument('--OEM2', type=str, default='', help='Optional OEM Field 2, an arbitrary length string')

    parser_print = subparsers.add_parser('parse', help='Parse a firmware policy and print in human readable form')
    parser_print.add_argument('filename', help='Filename to parse and print')

    options = parser.parse_args()

    print('Options: ', options)

    if options.action == 'create':
        nonceInt = int(options.NonceHex, 16)
        CreatePolicyFromParameters(options.PolicyFilename, options.Manufacturer,
                                   options.Product, options.SerialNumber, nonceInt, options.OEM1, options.OEM2)

    elif options.action == 'parse':
        PrintPolicy(options.filename)


if __name__ == '__main__':
    main()
