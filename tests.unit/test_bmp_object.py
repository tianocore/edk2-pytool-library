# @file
# Unit test for the bmp_object class
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.bmp_object import BmpObject
import io

'''
# to import an image into hex use this
import binascii
filename = image_path
with open(filename, 'rb') as f:
    content = f.read()
print(binascii.hexlify(content))
'''

hamburger = bytes.fromhex(('424d3603000000000000360000002800000010000000100000'
                           '00010018000000000000000000c30e0000c30e00000000000000000000fffffff7f7f7669ccc43'
                           '87c3307abd186ab12474b92877ba2477be1e70bc2473b83c81be337cbd4789c3fffffffffffff6'
                           'f6f6608fb92d70a11c666a0b57670d6e7f226fb54280b03a8f82228d661d886d0c6e990955a22e'
                           '78b986b1d8fffffff0f0f03b77ae257e57219b6920a87316a3661ba56a167c4e2b938d2cac8b19'
                           'ac7920b18110799f004f9d2f79baffffffffffff146a60157e4c21907026928e289daf33b3d23d'
                           'bee43fb8dd48b1d036a1a71e976824a47129997b11589cffffff78c0ec249bc9469bc5877cad5d'
                           '68854053721a335e182f571b2e592e4466515f799192ac9c82ad75c4c040a89edde6e826b0e54b'
                           'b4db9394b0223554233a58364c6a334c6d3451762f4d75304e742b4569273d5a435271c3bcd661'
                           'cbc15cbb9df1fafd7995a721395b173862113b692c4f7938557e3f5c7e4365893454812e4b7f32'
                           '4b7f34496f41506b9db2d0eaf6f5f5f5f54961791f42934a6fdc3e89c42aa1a6297e8e3a5cb534'
                           'b79a279183324bdd2945d52a38b5333c8c516890abddf4f8f8f82649703e61ca41a5a053a1a25d'
                           '9db15c9cbd599ac3568fb5588ead5a93aa468e9133867a2c3eb7384089f7f7f7fdfdfd38889369'
                           'a6b176a8cf5297d32b7fcd267bc92377c42e78b92777bf2975b93785cd4892d3589cba338281f7'
                           'f7f7ffffff7ab8d2589cd62f79be367cbb3381c61870bb1169b61c71b80d68b73177b3286da92a'
                           '7cc5297ecc5197cbf4f6f7fcfdfd559ad53e89cf2e7fc32674b6a9c2db2272b61c6eb4b0cbe914'
                           '68b00b5b9e9db6d0377cb72b7cc4277ccbe8f1f8fdfdff2b81cb3e89ccb7d0ec1c6fb4206dac2e'
                           '6ea51b68a90f60a51b69aa0e63a91461a31764a52470b22579c2eff4fbffffffb2d0eb3f89ca36'
                           '81c13c82bd4086c091b0ce3a74a5115c990b599bafcae6055ba3085ba17fa5ca8bacbefbfbfbff'
                           'fffff5f9fdaac7e05394cbb3cdea7faad06c9cc43f75a1a4b9cf125b98226ca7065ca40e65ae84'
                           'a8becad3d5fbfbfbfffffffffffffafbfcc0d1e0619bcd4e8fc8468ac43d80bb3576aa256fad20'
                           '6cab1565a8aac8e2e7e9ebf8f8f8ffffff'))

hamburger_lores = bytes.fromhex('424df60000000000000076000000280000001000000010'
                                '000000010004000000000080000000c30e0000c30e000000000000000000000000000000008000'
                                '008000000080800080000000800080008080000080808000c0c0c0000000ff0000ff000000ffff'
                                '00ff000000ff00ff00ffff0000ffffff00ff733333333333fff73333333333338ff33333323333'
                                '313ff32333bbbb33333f833733111138783fbb71111311113883f71111333311138ff319333333'
                                '999138f13333333333391ff377b3333333b33ff8b333333333333ffb3338338338333ff3383333'
                                '3333333ff83333833383377fff8388738333378ffff8733333338fff')

bad_header_burger = bytes.fromhex('434df600000000000000760000002800000010000000'
                                  '10000000010004000000000080000000c30e0000c30e0000000000000000000000000000000080'
                                  '00008000000080800080000000800080008080000080808000c0c0c0000000ff0000ff000000ff'
                                  'ff00ff000000ff00ff00ffff0000ffffff00ff733333333333fff73333333333338ff333333233'
                                  '33313ff32333bbbb33333f833733111138783fbb71111311113883f71111333311138ff3193333'
                                  '33999138f13333333333391ff377b3333333b33ff8b333333333333ffb3338338338333ff33833'
                                  '333333333ff83333833383377fff8388738333378ffff8733333338fff')

bad_size_burger = bytes.fromhex('424df60000000000000076000000280000001000000010'
                                '000000010004000000000080000000c30e0000c30e0000'
                                '0000000000000000000000000000800000800000008080'
                                '0080000000800080008080000080808000c0c0c0000000'
                                'ff0000ff000000ffff00ff000000ff00ff00ffff0000ff'
                                'ffff00ff733333333333fff73333333333338ff3333332'
                                '3333313ff32333bbbb33333f833733111138783fbb7111'
                                '1311113883f71111333311138ff319333333999138f133'
                                '33333333391ff377b3333333b33ff8b333333333333ffb'
                                '3338338338333ff33833333333333ff83333833383377f'
                                'ff8388738333378ffff873333333')


class TestBmpObject(unittest.TestCase):

    def test_good_header(self):
        file = io.BytesIO(hamburger)
        bmp = BmpObject(file)
        self.assertEqual(bmp.CharB, b'B', "B header should be accurate")
        self.assertEqual(bmp.CharM, b'M', "M header should be accurate")

    def test_lores_good_header(self):
        file = io.BytesIO(hamburger_lores)
        bmp = BmpObject(file)
        self.assertEqual(bmp.CharB, b'B', "B header should be accurate")
        self.assertEqual(bmp.CharM, b'M', "M header should be accurate")

    def test_get_width_height(self):
        file = io.BytesIO(hamburger)
        bmp = BmpObject(file)
        self.assertEqual(bmp.PixelWidth, 16, "This is a 16 by 16")
        self.assertEqual(bmp.PixelHeight, 16, "This is 16 by 16")

    def test_lores_get_width_height(self):
        file = io.BytesIO(hamburger_lores)
        bmp = BmpObject(file)
        self.assertEqual(bmp.PixelWidth, 16, "This is a 16 by 16")
        self.assertEqual(bmp.PixelHeight, 16, "This is 16 by 16")

    def test_get_bits(self):
        file = io.BytesIO(hamburger_lores)
        bmp = BmpObject(file)
        self.assertEqual(bmp.BitPerPixel, 4, "should be 4 bit aren't accurate")

    def test_get_24_bits(self):
        file = io.BytesIO(hamburger)
        bmp = BmpObject(file)
        self.assertEqual(bmp.BitPerPixel, 24, "24 bits aren't accurate")

    def test_bad_header(self):
        file = io.BytesIO(bad_header_burger)
        bmp = BmpObject(file)
        self.assertNotEqual(bmp.CharB, b'B', "B header should be accurate")
        self.assertEqual(bmp.BitPerPixel, 4, "24 bits aren't accurate")

    def test_bad_image(self):
        file = io.BytesIO(bad_size_burger)
        with self.assertRaises(Exception):
            BmpObject(file)  # we should keep reading pass the data
