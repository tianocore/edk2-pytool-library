# @file
# Helper lib to read and parse bitmap graphics files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for reading and parsing bitmap graphics files."""
import logging
import struct


class BmpColorMap(object):
    """An object representing a BMP_COLOR_MAP.

    Attributes:
        Blue (int): blue
        Green (int): green
        Red (int): red

    typedef struct {
        UINT8   Blue;
        UINT8   Green;
        UINT8   Red;
        UINT8   Reserved;
    } BMP_COLOR_MAP;
    """
    STATIC_SIZE = 4

    def __init__(self, filestream=None):
        """Inits an empty object or loads from an fs."""
        if filestream is None:
            self.Blue = 0
            self.Green = 0
            self.Red = 0
            self.Reserved = 0
        else:
            self.PopulateFromFileStream(filestream)

    def PopulateFromFileStream(self, fs):
        """Loads a bmp from a filestream.

        Args:
            fs (obj): A loaded filestream.

        Raises:
            (Exception): Invalid filestream
        """
        if fs is None:
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if (end - offset) < BmpColorMap.STATIC_SIZE:  # size of the bmp color map
            raise Exception("Invalid file stream size.  %d < Color map Size" % (end - offset))

        # read the Bmp Color Map
        self.Blue = struct.unpack("=B", fs.read(1))[0]
        self.Green = struct.unpack("=B", fs.read(1))[0]
        self.Red = struct.unpack("=B", fs.read(1))[0]
        self.Reserved = struct.unpack("=B", fs.read(1))[0]

    def Print(self):
        """Logs the object."""
        logger = logging.get(__name__)
        logger.info("BMP Color Map")
        logger.info("  Blue:           0x%X" % self.Blue)
        logger.info("  Green:          0x%X" % self.Green)
        logger.info("  Red:            0x%X" % self.Red)
        logger.info("  Reserved:       0x%X" % self.Reserved)

    def Write(self, fs):
        """Writes the object to a fs."""
        fs.write(struct.pack("=B", self.Blue))
        fs.write(struct.pack("=B", self.Green))
        fs.write(struct.pack("=B", self.Red))
        fs.write(struct.pack("=B", self.Reserved))


class BmpObject(object):
    """An object representing a BMP_IMAGE_HEADER.

    typedef struct {
        CHAR8         CharB;  < -- Start of FileHeader
        CHAR8         CharM;
        UINT32        Size;
        UINT16        Reserved[2];
        UINT32        ImageOffset;  <-- Start of pixel data relative to start of FileHeader
        UINT32        HeaderSize;  < -- Start of BmpHeader
        UINT32        PixelWidth;
        UINT32        PixelHeight;
        UINT16        Planes;          ///< Must be 1
        UINT16        BitPerPixel;     ///< 1, 4, 8, or 24
        UINT32        CompressionType;
        UINT32        ImageSize;       ///< Compressed image size in bytes
        UINT32        XPixelsPerMeter;
        UINT32        YPixelsPerMeter;
        UINT32        NumberOfColors;
        UINT32        ImportantColors;
    } BMP_IMAGE_HEADER;
    """
    STATIC_FILE_HEADER_SIZE = 14
    STATIC_IMAGE_HEADER_SIZE = 40

    def __init__(self, filestream=None):
        """Inits an empty object or loads from filestream."""
        self.logger = logging.getLogger(__name__)
        if filestream is None:
            self.CharB = 'B'
            self.CharM = 'M'
            self.Size = BmpObject.STATIC_STRUCT_SIZE
            self.Rsvd16_1 = 0
            self.Rsvd16_2 = 0
            self.ImageOffset = BmpObject.STATIC_STRUCT_SIZE
            self.HeaderSize = BmpObject.STATIC_STRUCT_SIZE
            self.PixelWidth = 0
            self.PixelHeight = 0
            self.Planes = 1
            self.BitPerPixel = 0
            self.CompressionType = 0
            self.ImageSize = 0
            self.XPixelsPerMeter = 0
            self.YPixelsPerMeter = 0
            self.NumberOfColors = 0
            self.ImportantColors = 0

            self.ImageData = None
            self._Padding = None
            self._PaddingLength = 0
            self.ColorMapList = []
        else:
            self.ImageData = None
            self.Padding = None
            self._PaddingLength = 0
            self.ColorMapList = []
            self.PopulateFromFileStream(filestream)

    def ExpectedColorMapEntires(self):
        """Returns expected entries depending on BitPerPixel."""
        if (self.BitPerPixel == 1):
            return 2
        elif (self.BitPerPixel == 4):
            return 16
        elif (self.BitPerPixel == 8):
            return 256
        else:
            return 0

    def PopulateFromFileStream(self, fs):
        """Method to un-serialize from a filestream.

        Args:
            fs (obj): filestream

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid size
            (Exception): Invalid Color map
            (Exception): Data remaining in buffer
        """
        if fs is None:
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        self.logger.debug("Bmp File size as determined by file is: 0x%X (%d)" % (
            end - offset, end - offset))

        if ((end - offset) < BmpObject.STATIC_FILE_HEADER_SIZE):  # size of the static file header data
            raise Exception(
                "Invalid file stream size.  %d < File Header Size" % (end - offset))

        # read the BMP File header
        self.CharB = struct.unpack("=c", fs.read(1))[0]
        self.CharM = struct.unpack("=c", fs.read(1))[0]
        self.Size = struct.unpack("=I", fs.read(4))[0]
        self.Rsvd16_1 = struct.unpack("=H", fs.read(2))[0]
        self.Rsvd16_2 = struct.unpack("=H", fs.read(2))[0]
        self.ImageOffset = struct.unpack("=I", fs.read(4))[0]

        if ((end - fs.tell()) < BmpObject.STATIC_IMAGE_HEADER_SIZE):
            raise Exception(
                "Invalid file stream size.  %d < Img Header Size" % (end - fs.tell()))

        # read the BMP Image Header
        self.HeaderSize = struct.unpack("=I", fs.read(4))[0]
        self.PixelWidth = struct.unpack("=I", fs.read(4))[0]
        self.PixelHeight = struct.unpack("=I", fs.read(4))[0]
        self.Planes = struct.unpack("=H", fs.read(2))[0]
        self.BitPerPixel = struct.unpack("=H", fs.read(2))[0]
        self.CompressionType = struct.unpack("=I", fs.read(4))[0]
        self.ImageSize = struct.unpack("=I", fs.read(4))[0]
        self.XPixelsPerMeter = struct.unpack("=I", fs.read(4))[0]
        self.YPixelsPerMeter = struct.unpack("=I", fs.read(4))[0]
        self.NumberOfColors = struct.unpack("=I", fs.read(4))[0]
        self.ImportantColors = struct.unpack("=I", fs.read(4))[0]

        if (self.Size < self.HeaderSize):
            raise Exception("Size can't be smaller than HeaderSize")

        if ((end - fs.tell()) < (self.Size - self.HeaderSize - BmpObject.STATIC_FILE_HEADER_SIZE)):
            raise Exception("Invalid file stream size (Size) 0x%X Less Than 0x%X" % (
                (end - fs.tell()), (self.Size - self.HeaderSize - BmpObject.STATIC_FILE_HEADER_SIZE)))

        StartOfImageData = offset + self.ImageOffset
        if (fs.tell() < StartOfImageData):

            # Handle any color maps
            if (self.ExpectedColorMapEntires() > 0):
                ColorMapCount = self.ExpectedColorMapEntires()
                if (self.NumberOfColors > 0) and (self.NumberOfColors != ColorMapCount):
                    self.logger.info("Current Code has untested support for limited color map, Good Luck. ")
                    self.logger.info("Expected Color Map Entries %d" % (ColorMapCount))
                    self.logger.info("Actual Color Map Entries %d" % (self.NumberOfColors))
                    ColorMapCount = self.NumberOfColors

                if ((StartOfImageData - fs.tell()) < (ColorMapCount * BmpColorMap.STATIC_SIZE)):
                    raise Exception("Color Map not as expected")

                # read all the color maps and append to the list
                for i in range(ColorMapCount):
                    self.ColorMapList.append(BmpColorMap(fs))

            # handle padding
            self._PaddingLength = StartOfImageData - fs.tell()
            self._Padding = fs.read(self._PaddingLength)

        self.ImageData = fs.read(self.Size - self.ImageOffset)

        if ((end - fs.tell()) > 0):
            raise Exception(
                "Extra Data at the end of BMP file - 0x%X bytes" % (end - fs.tell()))

    def Print(self, PrintImageData=False, PrintColorMapData=False):
        """Prints to logger.

        Args:
            PrintImageData (bool): Whether to print the ColorImage Data
            PrintColorMapData (bool): Whether to print the ColorMap List
        """
        self.logger.info("BMP")
        self.logger.info("  BMP File Header")
        self.logger.info("    CharB:           %s" % self.CharB)
        self.logger.info("    CharM:           %s" % self.CharM)
        self.logger.info("    Size:            0x%X (%d bytes)" % (self.Size, self.Size))
        self.logger.info("    RSVD[1]:         0x%X" % self.Rsvd16_1)
        self.logger.info("    RSVD[2]:         0x%X" % self.Rsvd16_2)
        self.logger.info("    ImageOffset:     0x%X (%d)" % (self.ImageOffset, self.ImageOffset))
        self.logger.info("  BMP Image Header")
        self.logger.info("    HeaderSize:      0x%X" % self.HeaderSize)
        self.logger.info("    PixelWidth:      0x%X (%d)" % (self.PixelWidth, self.PixelWidth))
        self.logger.info("    PixelHeight:     0x%X (%d)" % (self.PixelHeight, self.PixelHeight))
        self.logger.info("    Planes:          0x%X" % self.Planes)
        self.logger.info("    BitPerPixel:     %d" % self.BitPerPixel)
        self.logger.info("    CompressionType: 0x%X" % self.CompressionType)
        self.logger.info("    ImageSize:       0x%X (used for compressed images only)" % self.ImageSize)
        self.logger.info("    XPixelsPerMeter: %d" % self.XPixelsPerMeter)
        self.logger.info("    YPixelsPerMeter: %d" % self.YPixelsPerMeter)
        self.logger.info("    NumberOfColors:  %d" % self.NumberOfColors)
        self.logger.info("    ImportantColors: %d" % self.ImportantColors)
        # print color maps
        if (PrintColorMapData):
            for cm in self.ColorMapList:
                cm.Print()

        if (self._PaddingLength > 0):
            self.logger.info("  BMP Padding (0x%X bytes)" % self._PaddingLength)
            ndbl = memoryview(self._Padding).tolist()
            for index in range(len(ndbl)):
                if (index % 16 == 0):
                    self.logger.info("0x%04X -" % index),
                self.logger.info(" %02X" % ndbl[index]),
                if (index % 16 == 15):
                    self.logger.info("")
            self.logger.info("")

        if self.ImageData is not None and (PrintImageData):
            self.logger.info("  Bmp Image Data:    ")
            ndbl = memoryview(self.ImageData).tolist()
            for index in range(len(ndbl)):
                if (index % 16 == 0):
                    self.logger.info("0x%04X -" % index),
                self.logger.info(" %02X" % ndbl[index]),
                if (index % 16 == 15):
                    self.logger.info("")
            self.logger.info("")

    def Write(self, fs):
        r"""Serializes the Bmp object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        # Bmp File header
        fs.write(struct.pack("=c", self.CharB))
        fs.write(struct.pack("=c", self.CharM))
        fs.write(struct.pack("=I", self.Size))
        fs.write(struct.pack("=H", self.Rsvd16_1))
        fs.write(struct.pack("=H", self.Rsvd16_2))
        fs.write(struct.pack("=I", self.ImageOffset))

        # Bmp Img Header
        fs.write(struct.pack("=I", self.HeaderSize))
        fs.write(struct.pack("=I", self.PixelWidth))
        fs.write(struct.pack("=I", self.PixelHeight))
        fs.write(struct.pack("=H", self.Planes))
        fs.write(struct.pack("=H", self.BitPerPixel))
        fs.write(struct.pack("=I", self.CompressionType))
        fs.write(struct.pack("=I", self.ImageSize))
        fs.write(struct.pack("=I", self.XPixelsPerMeter))
        fs.write(struct.pack("=I", self.YPixelsPerMeter))
        fs.write(struct.pack("=I", self.NumberOfColors))
        fs.write(struct.pack("=I", self.ImportantColors))

        # Bmp Color Map
        for cm in self.ColorMapList:
            cm.Write(fs)

        # padding
        if (self._PaddingLength > 0):
            fs.write(self.Padding)

        # Pixel data
        if (self.ImageData):
            fs.write(self.ImageData)
